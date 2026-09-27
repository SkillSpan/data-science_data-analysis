"""
chunking.py
-----------
Turn a corpus of documentation files into retrievable chunks.

This is the part of retrieval that is easiest to get subtly wrong -- losing
text, splitting mid-sentence, emitting empty chunks -- and the part that is
fully testable without a network. It is therefore pure: no HTTP, no model calls.

Strategy: split the file on blank lines into paragraphs, then pack paragraphs
greedily up to `max_chars`. A paragraph longer than `max_chars` is split on
sentence boundaries, and a single over-long sentence is hard-split as a last
resort so no text is ever silently dropped. Consecutive chunks overlap, so a
fact that straddles a boundary is still retrievable from one of them.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from app.assistant.config import DEFAULT_CHUNK_CHARS, DEFAULT_CHUNK_OVERLAP

SUPPORTED_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

# Split after sentence-ending punctuation followed by whitespace. A lookbehind
# keeps the punctuation attached to the sentence it ends.
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?؟])\s+")

PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n")


@dataclass(frozen=True)
class Chunk:
    """One retrievable unit of documentation."""

    id: str
    """Stable identifier, `<source>#<index>`. Stable so a rebuilt index diff cleanly."""

    source: str
    """Corpus-relative path the chunk came from, for citing and for debugging."""

    text: str


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Pack sentences greedily; hard-split any single sentence that is too long."""
    pieces: list[str] = []
    buffer = ""

    for sentence in SENTENCE_BOUNDARY.split(paragraph):
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = f"{buffer} {sentence}".strip() if buffer else sentence
        if len(candidate) <= max_chars:
            buffer = candidate
            continue

        if buffer:
            pieces.append(buffer)
        buffer = sentence

    if buffer:
        pieces.append(buffer)

    # A single sentence can still exceed max_chars (a table row, a long list of
    # URLs). Split it mechanically rather than dropping it.
    result: list[str] = []
    for piece in pieces:
        while len(piece) > max_chars:
            result.append(piece[:max_chars])
            piece = piece[max_chars:]
        if piece:
            result.append(piece)

    return result


def _units(text: str, max_chars: int) -> list[str]:
    """Paragraph-sized pieces, with over-long paragraphs broken down further."""
    units: list[str] = []

    for raw in PARAGRAPH_BOUNDARY.split(text):
        paragraph = raw.strip()
        if not paragraph:
            continue

        if len(paragraph) <= max_chars:
            units.append(paragraph)
        else:
            units.extend(_split_long_paragraph(paragraph, max_chars))

    return units


def chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split one document's text into overlapping chunks.

    Each chunk is at most `max_chars` plus the carried overlap. Returns an empty
    list for blank input rather than a single empty chunk -- an empty chunk would
    embed to noise and could be retrieved, which is worse than nothing.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if not 0 <= overlap < max_chars:
        raise ValueError("overlap must be >= 0 and < max_chars")

    units = _units(text, max_chars)
    if not units:
        return []

    groups: list[list[str]] = []
    current: list[str] = []
    current_length = 0

    for unit in units:
        addition = len(unit) + (2 if current else 0)  # +2 for the "\n\n" joiner
        if current and current_length + addition > max_chars:
            groups.append(current)
            current = []
            current_length = 0
            addition = len(unit)

        current.append(unit)
        current_length += addition

    if current:
        groups.append(current)

    chunks: list[str] = []
    for index, group in enumerate(groups):
        body = "\n\n".join(group)
        if index > 0 and overlap:
            # Carry the tail of the previous group so a boundary-straddling fact
            # appears in full in at least one chunk.
            tail = groups[index - 1][-1][-overlap:]
            body = f"{tail}\n\n{body}"
        chunks.append(body.strip())

    return chunks


def load_documents(corpus_dir: str | Path) -> list[tuple[str, str]]:
    """
    Read every supported file under `corpus_dir` as (relative source, text).

    A missing directory yields an empty list rather than raising: the corpus
    does not exist yet, and that must degrade to "no retrieval" rather than
    break the service.
    """
    root = Path(corpus_dir)
    if not root.is_dir():
        return []

    documents: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        documents.append(
            (path.relative_to(root).as_posix(), path.read_text(encoding="utf-8"))
        )

    return documents


def build_chunks(
    corpus_dir: str | Path,
    *,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Chunk every document in the corpus, tagging each chunk with its source."""
    chunks: list[Chunk] = []

    for source, text in load_documents(corpus_dir):
        for index, body in enumerate(chunk_text(text, max_chars=max_chars, overlap=overlap)):
            chunks.append(Chunk(id=f"{source}#{index}", source=source, text=body))

    return chunks
