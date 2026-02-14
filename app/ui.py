# 파이썬 주소록에 상위 폴더 주소 등록해서 src폴더를(import 항목) 찾을 수 있도록
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# 웹 화면 생성 라이브러리 
import streamlit as st
from src.rag import answer_question

import uuid
import random
from src.storage import log_event



#  a/b 테스트 실험 설계도 작성

# DB에서 데이터를 가져올떄 구분자
EXPERIMENT = "topk_ab"
# 실험의 핵심 설정 k=3와 k=5로 설정
TOPK_BY_VARIANT = {"A": 2, "B": 4}


st.set_page_config(page_title="Mini RAG Q&A (A/B)", layout="wide")
st.title("Mini RAG: PDF Q&A + A/B (top_k)")

# st.markdown("Ask questions about the indexed PDF.")

# 마우스로 드래그해서 숫자를 조절하는 슬라이더 생성
#top_k = st.slider("Top-k retrieval", min_value=1, max_value=8, value=4)


# st.session_state 는 브라우저를 새로고침해도 데이터를 기억하게 해주는 streamlit의 저장소
# 아직 ID가 발급 안된 사용자라면 고유번호를 생성(uuid,uuid4)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# random choice를 통해 사용자를 A로 보낼지 B로 보낼지 결정(A/B 테스트의 핵심)
if "variant" not in st.session_state:
    st.session_state.variant = random.choice(["A", "B"])

# variant 확인
variant = st.session_state.variant
# 확인된 variant에 따라 k 설정
top_k = TOPK_BY_VARIANT[variant]



# 화면에 variant 표시
st.caption(f"Experiment: {EXPERIMENT} | Session: {st.session_state.session_id[:8]} | Variant: {variant} | top_k={top_k}")

# 질문 입력 박스 생성
question = st.text_input("Enter your question:")

if "last_result" not in  st.session_state:
    st.session_state.last_result = None



if st.button("Ask") and question:
    # 로딩 애니메이션 삽입(돌아가는)
    with st.spinner("Thinking..."):
        # rag.py 함수 호출
        answer, citations, sources, elapsed, source_pages = answer_question(question, top_k = top_k)

    latency_ms = int(elapsed * 1000)

    # 질문 이벤트 1회 DB에 로깅, experiments/events.db
    log_event(
        session_id=st.session_state.session_id,
        experiment=EXPERIMENT,
        variant=variant,
        question=question,
        top_k=top_k,
        latency_ms=latency_ms,
        citations=citations,
        source_pages=source_pages,
        # DB 용량을 적정 수준으로 유지하기 위해.
        answer=answer[:2000],
        user_vote=None,
    )



# 결과 출력부
    # 단순히 RAG 결과를 보여주는 것에서 나아가 이 결과에 대한 유저의 만족도를 수집하기 위함
    # 피드백 숮비을 통해 실제 서비스 운영과 성능 개선(RLHF의 기초)

    # 중간 크기의 제목
    st.subheader("Answer")
    # write, gpt 답변을 화면에 출력
    st.write(answer)
    st.write(citations)

    st.subheader("Sources")
    for i, s in enumerate(sources, 1):
        # 글자를 굵게 표시 **...**
        st.markdown(f"**{i}. Page {s['page']}**")
        st.write(s["snippet"])
    # 최 하단 작은 폰트로
    st.caption(f"Latency: {elapsed:.2f}s")



    # 만족도 투표을 위한 session state에 임시 저장 
    st.session_state.last_result = {
        "question": question,
        "answer": answer,
        "citations": citations,
        "source_pages": source_pages,
        "latency_ms": latency_ms,
        "top_k": top_k,
        "variant": variant,
    }




# 피드백 버튼 로직
if st.session_state.last_result is not None:
    st.divider()
    st.subheader("Rate the last answer")

    # 화면을 2개로 나눠서 보튼 두개를 가로로 배치
    c1, c2 = st.columns(2)
    with c1:
        # 사용자가 UP 버튼을 누르면:
        if st.button("👍 Good"):
            # session_state에서 데이터 꺼내기
            r = st.session_state.last_result
            
            log_event(
                session_id=st.session_state.session_id,
                experiment=EXPERIMENT,
                variant=r["variant"],
                question=r["question"],
                top_k=r["top_k"],
                latency_ms=r["latency_ms"],
                citations=r["citations"],
                source_pages=r["source_pages"],
                answer=r["answer"][:2000],
                user_vote="up", # UP이라고 DB에 기록
            )
            st.success("Logged 👍")

    with c2:
        if st.button("👎 Bad"):
            r = st.session_state.last_result
            log_event(
                session_id=st.session_state.session_id,
                experiment=EXPERIMENT,
                variant=r["variant"],
                question=r["question"],
                top_k=r["top_k"],
                latency_ms=r["latency_ms"],
                citations=r["citations"],
                source_pages=r["source_pages"],
                answer=r["answer"][:2000],
                user_vote="down",
            )
            st.success("Logged 👎")
# 얇은 줄을 통해 시각적으로 분리해 주는 역할
st.divider()
st.caption("Tip: Variant is fixed per session to avoid mixing A/B within one user session.")