import argparse
import time
from typing import List, Tuple

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from src.config import CHROMA_DIR, EMBEDDING_MODEL, CHAT_MODEL, OPENAI_API_KEY



SYSTEM_PROMPT = """You are a helpful assistant.
Answer ONLY using the provided context.
If the context does not contain the answer, say exactly:
I don't know based on the provided document.
"""

USER_TEMPLATE = """Context:
{context}

Question: {question}
"""



def format_sources(docs) -> List[dict]:
    """Return normalized source info for UI/CLI"""
    sources = []
    # 하나의 문서 조각(d) 안에서 page_content(텍스트) 와 metadata가 있다.
    for d in docs:
        # meta데이터에는 페이지, 파일이름등의 정보가 있는데 각 조각마다 이것을 가져오며 없으면 {}
        md = d.metadata or {}
        # 딕셔너리 값 안전하게 꺼내기
        page = md.get("page")
        # None + 숫자 와 같은 경우 계산오류가 생기기 때문에 이를 방지하기 위함
        page_display = (page + 1) if isinstance(page, int) else page
        # 문서(d)가 내용이 없을 경우 공백으로 대체, 불필요한 공백제거, 줄바꿈 공백으로 변환.
        snippet = (d.page_content or "").strip().replace("\n"," ")
        # 글자수 240 제한, 초과시 ... 표시 
        snippet = snippet[:240] + ("..." if len(snippet) > 240 else "")
        sources.append(
            {
                "page": page_display,
                "source": md.get("source"),
                "snippet": snippet,
            }
        )
    return sources



def build_context(docs) -> str:
    parts = []
    for i, d in enumerate(docs ,1):
        md = d.metadata or {}
        page = md.get("page")
        page_display = (page + 1) if isinstance(page, int) else page
        text = (d.page_content or "").strip()
        parts.append(f"[source {i} | page {page_display}]\n{text}")
    # 조각 사이에 엔터*2 후에 합치기
    return "\n\n".join(parts)



# citation을 모델에 맡기지 않고 시스템이 확보한 정확한 메타데이터를 표시
def citations_line(docs) -> str:
    """Citations are generated from retrieved docs (not by the model)."""
    pages = []
    for d in docs:
        page = (d.metadata or {}).get("page")
        if isinstance(page, int):
            pages.append(page + 1)  # 0-based → 1-based
    pages = sorted(set(pages))
    if not pages:
        return "Citations: (none)"
    return "Citations: " + ", ".join([f"p.{p}" for p in pages])



# RAG 프로세스의 본체, 질문을 받아 검색->조립->생성
# top_k는 가장 관련있는 문서 조각의 수 설정 / 이것을 답변, 출처리스트, 걸린시간 형태로 돌려주겠다는 표시
def answer_question(question: str, top_k: int =4) -> Tuple[str, List[dict], float]:
    if not OPENAI_API_KEY:
        raise RuntimeError("conld not find OPENAI_API_KEY, please set the .env file")
    
    t0 = time.time()

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    db = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="docs",
    )

    # DB를 검색기 모드로 변경
    retriever = db.as_retriever(search_kwargs={"k":top_k})
    # 짊문과 좌표가 가장 가까운 4조각 가져옴
    docs = retriever.invoke(question)


    # 참고서 만들기(Augmentation)
    context = build_context(docs)

    # 질의, temperature는 ai가 헛소리 못하게 창의성을 0으로 만듬
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(context=context, question=question)},
    ]

    # invoke는 입력을 넣고 결과가 나올 때까지 기다리는 동기식 호출 
    # .stream() 은 답변을 GPT처럼 한글짜씩 실시간으로 받아온다
    resp = llm.invoke(messages)
    answer = resp.content.strip()

    citations = citations_line(docs)
    dt = time.time() - t0
    return answer, citations, format_sources(docs), dt



def main():
    # CLI 인터페이스 작성, 터미널에서 명령어로 실행할 수 있게 함
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True, help="Question to ask")
    ap.add_argument("--top_k", type=int, default=4, help="Number of retrieved chunks")
    args = ap.parse_args()

    answer, citations, sources, elapsed = answer_question(args.question, args.top_k)


    print("\n=== Answer ===")
    print(answer)
    print(citations)

    print("\n=== Sources ===")
    for i, s in enumerate(sources, 1):
        print(f"{i}, page={s.get('page')} | {s.get('snippet')}")

    print(f"\n[OK] elapsed={elapsed:.2f}s | top_k={args.top_k}")


if __name__ == "__main__":
    main()