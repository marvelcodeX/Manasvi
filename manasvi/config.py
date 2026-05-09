import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    DATABASE_PATH = Path(os.getenv("MANASVI_DB_PATH", BASE_DIR / "instance" / "manasvi.db"))
    KNOWLEDGE_BASE_PATH = Path(os.getenv("MANASVI_KB_PATH", BASE_DIR / "data" / "knowledge_base.txt"))
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ENABLE_VECTOR_RAG = os.getenv("MANASVI_ENABLE_VECTOR_RAG", "0") == "1"
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
