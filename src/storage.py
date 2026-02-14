import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("experiments") / "events.db"

# 스키마 작성(컬럼작성)
SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  session_id TEXT,
  experiment TEXT,
  variant TEXT,
  question TEXT,
  top_k INTEGER,
  latency_ms INTEGER,
  citations TEXT,
  source_pages TEXT,
  answer TEXT,
  user_vote TEXT  
);
"""

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn

def log_event(
    session_id: str,
    experiment: str,
    variant: str,
    question: str,
    top_k: int,
    latency_ms: int,
    citations: str,
    source_pages: str,
    answer: str,
    user_vote: str | None = None,
):
    ts = datetime.utcnow().isoformat()
    conn = get_conn()
    with conn:
        # (?,) 는 입력값을 단순한 글자로 취습, SQL 인젝션 공격을 막음, Parameter binding
        conn.execute(
            """
            INSERT INTO events (ts, session_id, experiment, variant, question, top_k, latency_ms, citations, source_pages, answer, user_vote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, session_id, experiment, variant, question, top_k, latency_ms, citations, source_pages, answer, user_vote),         
        )
    conn.close()
