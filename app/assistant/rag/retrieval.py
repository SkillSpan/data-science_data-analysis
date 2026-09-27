import logging

from app.assistant.config import settings
from app.assistant.rag.embeddings import QUERY_TASK, EmbeddingError, GeminiEmbedder
from app.assistant.rag.index import IndexUnavailable, Retrieved, VectorIndex

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, *, index_path: str, model: str, top_k: int, min_score: float, embedder=None) -> None:
        self.index_path = index_path
        self.model = model
        self.top_k = top_k
        self.min_score = min_score
        self._embedder = embedder
        self._index: VectorIndex | None = None

    @classmethod
    def from_settings(cls) -> "Retriever":
        return cls(
            index_path=settings.index_path,
            model=settings.embedding_model,
            top_k=settings.top_k,
            min_score=settings.min_score,
        )

    def _load(self) -> VectorIndex | None:
        if self._index is not None:
            return self._index
        try:
            self._index = VectorIndex.load(self.index_path, expected_model=self.model)
        except IndexUnavailable as exc:
            logger.error("Assistant retrieval index unavailable: %s", exc)
            return None
        logger.info("Assistant retrieval index loaded: %d chunks", len(self._index))
        return self._index

    def _query_embedder(self):
        if self._embedder is None:
            self._embedder = GeminiEmbedder(model=self.model, task_type=QUERY_TASK)
        return self._embedder

    @property
    def available(self) -> bool:
        index = self._load()
        return index is not None and len(index) > 0

    def retrieve(self, question: str) -> list[Retrieved]:
        index = self._load()
        if index is None or len(index) == 0:
            return []
        try:
            hits = index.query(
                question,
                self._query_embedder(),
                top_k=self.top_k,
                min_score=self.min_score,
            )
        except EmbeddingError as exc:
            logger.warning("Assistant retrieval failed: %s", exc)
            return []
        logger.info(
            "Assistant retrieved %d chunk(s): %s",
            len(hits),
            ", ".join(f"{hit.chunk.id} ({hit.score:.3f})" for hit in hits) or "none",
        )
        return hits

    def context_for(self, question: str) -> str | None:
        hits = self.retrieve(question)
        if not hits:
            return None
        return "\\n\\n".join(hit.chunk.text for hit in hits)
