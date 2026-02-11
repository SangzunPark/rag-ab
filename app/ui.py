# 파이썬 주소록에 상위 폴더 주소 등록해서 src폴더를(import 항목) 찾을 수 있도록
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# 웹 화면 생성 라이브러리 
import streamlit as st
from src.rag import answer_question

st.set_page_config(page_title="Boutique RAG Q&A", layout="wide")

st.title("PROXIMITY: Boutique RAG Engine")

st.markdown("Ask questions about the indexed PDF.")

# 질문 입력 박스 생성
question = st.text_input("Enter your question:")
# 마우스로 드래그해서 숫자를 조절하는 슬라이더 생성
top_k = st.slider("Top-k retrieval", min_value=1, max_value=8, value=4)

if st.button("Ask") and question:
    # 로딩 애니메이션 삽입(돌아가는)
    with st.spinner("Thinking..."):
        # rag.py 함수 호출
        answer, citations, sources, elapsed = answer_question(question, top_k = top_k)

    # 중간 크기의 제목
    st.subheader("Answer")
    # write, 텍스트를 화면에 출력
    st.write(answer)
    st.write(citations)

    st.subheader("Sources")
    for i, s in enumerate(sources, 1):
        # 글자를 굵게 표시 **...**
        st.markdown(f"**{i}. Page {s['page']}**")
        st.write(s["snippet"])
    # 최 하단 작은 폰트로
    st.caption(f"Latency: {elapsed:.2f}s")