import argparse
from pathlib import Path
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# langchain-chroma로 변경 예정
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from src.config import CHROMA_DIR, EMBEDDING_MODEL, CHUNK_OVERLAP, CHUNK_SIZE, OPENAI_API_KEY

def ingest_pdf(pdf_path: Path) -> None:
    if not OPENAI_API_KEY:
        # return 과 다른점은 raise는 발생즉시 작업 종료
        raise RuntimeError(
            "There's no API kye please check a .env file"
        )
    

    t0 = time.time()

    # PDF load 
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()

    # chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)

    # embedding: vector 변환
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # save to Chroma
    db = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="docs",
    )

    # vector 변환 시작
    db.add_documents(chunks)
    # 하드(chroma DB)에 저장 확정 명령 / 현재는 persist를 사용하지 않아도 자동으로 저장
    db.persist()

    dt = time.time() - t0


    print("[OK] PDF:", pdf_path)
    print("[OK] Pages loaded:", len(docs))
    print("[OK] Chunks created:", len(chunks))
    print("[OK] Chunk params:", {"chunk_size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP})
    print("[OK] Embedding model:", EMBEDDING_MODEL)
    print("[OK] Saved Chroma DB to:", CHROMA_DIR)
    print(f"[OK] Elapsed: {dt:.2f}s")

def main():
    # 터미널에서 사용자가 입력하는 옵션을 해석하는 툴
    ap = argparse.ArgumentParser()
    # --pdf 를 파일경로의 라벨로 사용할 것이고, required=True이기 때문에 사용하지 않으면 에러 표시, 
    # 그리고 개발 협업을 위해 help를 입력하면 이것에 대한 설명을 볼 수 있게 함
    ap.add_argument("--pdf", required=True, help="Path to a PDF file")
    # 실제 입력값 추출
    args = ap.parse_args()
    # 입력값을 파이썬 객체로 변환
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found {pdf_path}")
    
    # 변환 함수 실행
    ingest_pdf(pdf_path)

if __name__ == "__main__":
    main()