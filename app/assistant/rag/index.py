"""
index.py
--------
An in-process vector index over the documentation corpus.

Deliberately *not* a hosted vector database: the corpus is one platform's
documentation -- hundreds of chunks, not millions -- so a JSON file plus cosine
similarity is enough, costs nothing, and adds no dependency or service to
operate. If the corpus ever grows past a few thousand chunks, this is the module
to replace; nothing else needs to change.

The index records the embedding model that produced it, and loading an index
built by a different model is refused rather than tolerated. Mismatched vectors
do not raise -- they silently return nonsense -- which is the worst possible
failure mode for a system whose whole job is grounding.
"""

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from app.assistant.rag.chunking import Chunk
from app.assistant.rag.embeddings import Embedder, EmbeddingError

logger = logging.getLogger(__name__)

FORMAT_VERSION = 1

# Vectors are rounded before serialising. Full float repr roughly triples the
# file size and changes nothing about the ranking.
VECTOR_PRECISION = 6


class IndexUnavailable(Exception):
    """The index is missing, unreadable, or was built with a different model."""


@dataclass(frozen=True)
class Retrieved:
    """One search hit."""

    chunk: Chunk
    score: float


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    """Cosine similarity. Returns 0.0 for a zero-length vector."""
    if len(left) != len(right):
        raise ValueError("embedding vectors must have the same dimensions")
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0

    for a, b in zip(left, right):
        dot += a * b
        left_norm += a * a
        right_norm += b * b

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


class VectorIndex:
    """Chunks plus their vectors, searchable by cosine similarity."""

    def __init__(
        self,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
        model: str,
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")

        self.chunks = list(chunks)
        self.vectors = [list(vector) for vector in vectors]
        self.model = model

    def __len__(self) -> int:
        return len(self.chunks)

    @classmethod
    def build(cls, chunks: Sequence[Chunk], embedder: Embedder, model: str) -> "VectorIndex":
        """Embed every chunk and return a ready index."""
        if not chunks:
            return cls([], [], model)

        vectors = embedder.embed([chunk.text for chunk in chunks])
        return cls(chunks, vectors, model)

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "format_version": FORMAT_VERSION,
            "model": self.model,
            "chunks": [
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "text": chunk.text,
                    "vector": [round(value, VECTOR_PRECISION) for value in vector],
                }
                for chunk, vector in zip(self.chunks, self.vectors)
            ],
        }

        destination.write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, *, expected_model: str | None = None) -> "VectorIndex":
        source = Path(path)
        if not source.is_file():
            raise IndexUnavailable(f"no index at {source}")

        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IndexUnavailable(f"{source} could not be read: {exc}") from exc

        if payload.get("format_version") != FORMAT_VERSION:
            raise IndexUnavailable(
                f"{source} has format version {payload.get('format_version')!r}, "
                f"expected {FORMAT_VERSION}. Rebuild it."
            )

        model = payload.get("model")
        if expected_model and model != expected_model:
            raise IndexUnavailable(
                f"{source} was built with {model!r} but the configured embedding "
                f"model is {expected_model!r}. Rebuild it -- vectors from different "
                "models are not comparable."
            )

        entries = payload.get("chunks") or []
        chunks = [Chunk(id=e["id"], source=e["source"], text=e["text"]) for e in entries]
        vectors = [e["vector"] for e in entries]

        return cls(chunks, vectors, model or "")

    def search(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        min_score: float = 0.0,
    ) -> list[Retrieved]:
        """Return the `top_k` best chunks, best first, above `min_score`."""
        if top_k <= 0 or not self.chunks:
            return []

        scored = [
            Retrieved(chunk=chunk, score=_cosine(vector, candidate))
            for chunk, candidate in zip(self.chunks, self.vectors)
        ]
        scored.sort(key=lambda hit: hit.score, reverse=True)

        return [hit for hit in scored[:top_k] if hit.score >= min_score]

    def query(
        self,
        question: str,
        embedder: Embedder,
        *,
        top_k: int,
        min_score: float = 0.0,
    ) -> list[Retrieved]:
        """Embed a question and search. Thin wrapper over `search`."""
        vectors = embedder.embed([question])
        if not vectors:
            raise EmbeddingError("the question could not be embedded")

        return self.search(vectors[0], top_k=top_k, min_score=min_score)
