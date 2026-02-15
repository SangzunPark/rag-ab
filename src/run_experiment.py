import argparse
import json
import uuid
from pathlib import Path

from src.rag import answer_question
from src.storage import log_event

EXPERIMENT = "topk_ab_offline_k2_k4"
TOPK_BY_VARIANT = {"A": 2, "B": 4}


def main():
    # argparse는 파이썬 프로그램을 실행할 때 터미널 을 통해 옵션 재료를 직접 설정할 수 있게 하는 도구
    # .ArgumentParse() 분석기 생성
    ap = argparse.ArgumentParser()
    # 메뉴 츄가(인자 정의), 이름, 타입, 기본설정, 도움말
    ap.add_argument("--questions", default="experiments/test_questions.json")
    ap.add_argument("--limit", type=int, default=0, help="0 means no limit")
    # 설정을 모은 최종 파싱기(바구니) 생성
    args = ap.parse_args()

    # json 파일의 질문 리스트를 파이썬의 question 변수로 옮김(리스트)
    # args.questions 에 있는 주소를 Path로 변환
    questions_path = Path(args.questions)
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    if args.limit and args.limit > 0:
        questions = questions[: args.limit]

    # uuid는 128비트 고유 식별 번호 생성, uuid4s는 완전 랜점 방식
    # run_experiment.py를 실행할때 마다 새로운 랜덤 번호 생성-> 특정 세선을 구별할 수 있음
    session_id = str(uuid.uuid4())
    print(f"[OK] session_id={session_id} | questions={len(questions)}")

    for q in questions:
        for variant in ["A", "B"]:
            top_k = TOPK_BY_VARIANT[variant]
            answer, citations, sources, elapsed, source_pages = answer_question(q, top_k=top_k)

            latency_ms = int(elapsed * 1000)
            log_event(
                session_id=session_id,
                experiment=EXPERIMENT,
                variant=variant,
                question=q,
                top_k=top_k,
                latency_ms=latency_ms,
                citations=citations,
                source_pages=source_pages,
                answer=answer[:2000],
                user_vote=None,  # 오프라인 실행은 투표 없음
            )

            print(f"[OK] {variant} top_k={top_k} latency_ms={latency_ms} q={q[:60]}")

    print("[DONE] Logged into experiments/events.db")


if __name__ == "__main__":
    main()
