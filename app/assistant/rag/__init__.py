"""
rag
---
Retrieval-augmented generation for the SkillSpan assistant.

The corpus is SkillSpan's own documentation, and it does not exist yet -- see
`CORPUS.md` at the service root. Nothing in this package invents content: with an
empty corpus the service behaves exactly as it did before retrieval existed,
which is the point of gating it behind RAG_ENABLED.

Submodules are deliberately not re-exported here, so `import rag` does not drag
in the Google SDK. Import what you need explicitly:

    from app.assistant.rag.chunking import build_chunks
    from app.assistant.rag.index import VectorIndex
"""
