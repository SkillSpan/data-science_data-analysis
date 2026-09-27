"""
ingest.py
---------
Build the retrieval index from the documentation corpus.

    python -m rag.ingest --stats     # chunk the corpus and report; no API calls
    python -m rag.ingest --check     # verify the embedding model works, then stop
    python -m rag.ingest             # build and save the index

`--check` exists because provider model names in this project have already gone
stale once (see the note in config.py). An embedding model that 404s is far
cheaper to discover from a one-line command than from a production request.

Run `--stats` first: it costs nothing and tells you whether the corpus is even
there before you spend an API call on it.
"""

import argparse
import logging
import sys
from collections import Counter

from app.assistant.config import settings
from app.assistant.rag.chunking import build_chunks
from app.assistant.rag.embeddings import DOCUMENT_TASK, EmbeddingError, GeminiEmbedder
from app.assistant.rag.index import VectorIndex

logger = logging.getLogger("rag.ingest")

# A short probe used by --check. Only its embedding is wanted, not its content.
PROBE_TEXT = "How is the SkillSpan Readiness Score calculated?"


def _report_corpus(corpus_dir: str) -> list:
    """Chunk the corpus and print what was found. No network, no cost."""
    chunks = build_chunks(corpus_dir)

    if not chunks:
        logger.error(
            "No chunks found under %r. The corpus is empty or missing.\n"
            "Retrieval cannot work without documentation -- see CORPUS.md at the "
            "service root for what belongs there and who writes it. Nothing has "
            "been built or changed.",
            corpus_dir,
        )
        return []

    per_source = Counter(chunk.source for chunk in chunks)
    logger.info("%d chunks from %d document(s):", len(chunks), len(per_source))
    for source, count in sorted(per_source.items()):
        logger.info("  %-50s %d", source, count)

    sizes = [len(chunk.text) for chunk in chunks]
    logger.info(
        "chunk size: min=%d mean=%d max=%d characters",
        min(sizes),
        sum(sizes) // len(sizes),
        max(sizes),
    )

    return chunks


def _check_embedder(model: str) -> int:
    """Prove the embedding model actually answers before building anything."""
    embedder = GeminiEmbedder(model=model, task_type=DOCUMENT_TASK)

    try:
        vectors = embedder.embed([PROBE_TEXT])
    except EmbeddingError as exc:
        logger.error("Embedding check failed: %s", exc)
        logger.error(
            "If this is a NOT_FOUND, the model name is stale. Override it with "
            "EMBEDDING_MODEL in the environment."
        )
        return 1

    logger.info("Embedding check passed: %s -> %d dimensions", model, len(vectors[0]))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rag.ingest",
        description="Build the retrieval index from the SkillSpan documentation corpus.",
    )
    parser.add_argument("--corpus", default=settings.corpus_dir, help="corpus directory")
    parser.add_argument("--index", default=settings.index_path, help="index output path")
    parser.add_argument("--model", default=settings.embedding_model, help="embedding model")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="chunk the corpus and report, without calling any API",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the embedding model responds, then stop",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )

    if args.check:
        return _check_embedder(args.model)

    chunks = _report_corpus(args.corpus)
    if not chunks:
        return 2

    if args.stats:
        logger.info("--stats only: no index written.")
        return 0

    try:
        index = VectorIndex.build(chunks, GeminiEmbedder(model=args.model), args.model)
    except EmbeddingError as exc:
        logger.error("Embedding failed, index not written: %s", exc)
        return 1

    index.save(args.index)
    logger.info("Wrote %d chunks to %s", len(index), args.index)

    return 0


if __name__ == "__main__":
    sys.exit(main())
