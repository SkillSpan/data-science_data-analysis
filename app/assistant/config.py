import os
from dataclasses import dataclass

PROVIDER_TIMEOUT_SECONDS = 8.0
MAX_OUTPUT_TOKENS = 1024

GEMINI_MODEL = os.getenv("GEMINI_CHAT_MODEL") or "gemini-3.6-flash"
GROQ_MODEL = os.getenv("GROQ_CHAT_MODEL") or "openai/gpt-oss-120b"
CEREBRAS_MODEL = os.getenv("CEREBRAS_CHAT_MODEL") or "gpt-oss-120b"
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
PROVIDER_FAILOVER_ORDER = ("groq", "gemini", "cerebras")

EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_TOP_K = 4
DEFAULT_MIN_SCORE = 0.45
DEFAULT_CHUNK_CHARS = 1200
DEFAULT_CHUNK_OVERLAP = 200


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name) or default)
    except ValueError:
        return default
    return value if value > 0 else default


def _score(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name) or default)
    except ValueError:
        return default
    return value if 0.0 <= value <= 1.0 else default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    groq_api_key: str | None
    cerebras_api_key: str | None
    rag_enabled: bool
    corpus_dir: str
    index_path: str
    embedding_model: str
    top_k: int
    min_score: float

    @property
    def available_providers(self) -> list[str]:
        configured = {
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
            "cerebras": self.cerebras_api_key,
        }
        return [name for name in PROVIDER_FAILOVER_ORDER if configured[name]]

    @property
    def retrieval_configured(self) -> bool:
        return self.rag_enabled and bool(self.gemini_api_key)


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        cerebras_api_key=os.getenv("CEREBRAS_API_KEY"),
        rag_enabled=_flag(os.getenv("RAG_ENABLED")),
        corpus_dir=os.getenv("CORPUS_DIR") or "app/assistant/corpus",
        index_path=os.getenv("RAG_INDEX_PATH") or "app/assistant/corpus/index.json",
        embedding_model=os.getenv("EMBEDDING_MODEL") or EMBEDDING_MODEL,
        top_k=_positive_int("RAG_TOP_K", DEFAULT_TOP_K),
        min_score=_score("RAG_MIN_SCORE", DEFAULT_MIN_SCORE),
    )


settings = load_settings()
