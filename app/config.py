from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

VECTOR_TOP_K = 10
RERANK_TOP_K = 5

SIMILARITY_THRESHOLD = 0.72

TRUSTED_DOMAINS = [
    "law.go.kr",
    "g2b.go.kr",
    "moe.go.kr",
]