"""
embeddings.py
-------------
Embedding adapter.

`Embedder` is a Protocol, not a base class, so the index and the retrieval path
can be tested with a deterministic fake and no network call. The only concrete
implementation talks to Gemini, because the service already holds a
GEMINI_API_KEY for chat -- retrieval therefore adds no new vendor.

Documents and queries must be embedded with different task types. Gemini's
retrieval quality depends on it, and using one type for both quietly degrades
results without erroring, so the two are separate instances rather than one
shared default.
"""

import logging
from typing import Protocol, Sequence

from app.assistant.config import EMBEDDING_MODEL, settings

logger = logging.getLogger(__name__)

DOCUMENT_TASK = "RETRIEVAL_DOCUMENT"
QUERY_TASK = "RETRIEVAL_QUERY"

# Gemini accepts a batch of contents per call. Kept modest so one oversized
# request cannot fail the whole ingest.
DEFAULT_BATCH_SIZE = 32


class EmbeddingError(Exception):
    """Raised when embeddings cannot be produced."""


class Embedder(Protocol):
    """Anything that can turn text into vectors, one per input string."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class GeminiEmbedder:
    """Embeddings via Google Gemini."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        task_type: str = DOCUMENT_TASK,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.model = model or settings.embedding_model or EMBEDDING_MODEL
        self.api_key = api_key or settings.gemini_api_key
        self.task_type = task_type
        self.batch_size = batch_size

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key:
            raise EmbeddingError("GEMINI_API_KEY is not configured")

        # Imported lazily so importing this module stays cheap, and so a missing
        # optional dependency surfaces as an EmbeddingError at call time rather
        # than an ImportError at startup.
        from google import genai
        from google.genai import types

        vectors: list[list[float]] = []

        try:
            client = genai.Client(api_key=self.api_key)

            for start in range(0, len(texts), self.batch_size):
                batch = list(texts[start : start + self.batch_size])
                response = client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type=self.task_type),
                )

                embeddings = getattr(response, "embeddings", None)
                if not embeddings:
                    raise EmbeddingError(f"{self.model} returned no embeddings")

                if len(embeddings) != len(batch):
                    raise EmbeddingError(
                        f"{self.model} returned {len(embeddings)} embeddings for "
                        f"{len(batch)} inputs"
                    )

                vectors.extend(list(item.values) for item in embeddings)

        except EmbeddingError:
            raise
        except Exception as exc:  # noqa: BLE001 - any SDK/network failure
            raise EmbeddingError(f"{self.model}: {exc}") from exc

        return vectors
