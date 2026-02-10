from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "data" / "docs"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# 키가 없으면 빈 문자열을 넣을것
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 800
# 문맥 유지를 위해
CHUNK_OVERLAP = 120
