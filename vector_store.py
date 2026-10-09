"""
vector_store.py  -  OUR OWN SMALL VECTOR DATABASE
=================================================

A vector database stores pieces of text together with their embeddings
(lists of numbers that capture meaning), and finds the pieces whose numbers
are closest to a question's numbers.

Big companies use products like Chroma, Pinecone or pgvector for millions of
pieces. For a few hundred pieces, we can do the same job ourselves in a few lines:

- SAVE: write every chunk + its numbers + where it came from into one file
        (brand_db/knowledge_base.json).
- SEARCH: compare the question's numbers with every chunk's numbers using
        "cosine similarity" - a score from 0 (unrelated) to 1 (same meaning) -
        and return the highest-scoring chunks.

numpy is a maths toolbox that does these comparisons for all chunks at once, very fast.
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np

STORE_FILE = Path(__file__).parent / "brand_db" / "knowledge_base.json"


def save(chunks, vectors, embed_model):
    """
    Save the knowledge base to disk, replacing any old one.
    chunks:  list of {"text", "source", "page", "chunk"}
    vectors: list of embeddings, one per chunk, in the same order
    """
    STORE_FILE.parent.mkdir(exist_ok=True)
    data = {
        "embed_model": embed_model,                    # remember which model made the numbers
        "built_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chunks": [dict(c, vector=list(map(float, v))) for c, v in zip(chunks, vectors)],
    }
    STORE_FILE.write_text(json.dumps(data), encoding="utf-8")


def load():
    """Read the knowledge base from disk. Returns None if it hasn't been built yet."""
    if not STORE_FILE.exists():
        return None
    return json.loads(STORE_FILE.read_text(encoding="utf-8"))


def search(question_vector, top_k=4, only_source=None):
    """
    Return the top_k chunks most similar in meaning to the question, best first.
    Each result: {"text", "source", "page", "score"}
    only_source: optionally search one document only, e.g. "customer_faq.md".
    """
    data = load()
    if not data or not data["chunks"]:
        return []

    chunks = [c for c in data["chunks"] if only_source in (None, c["source"])]
    if not chunks:
        return []

    # Put all chunk vectors in one table (one row per chunk) so numpy can compare them in one go.
    matrix = np.array([c["vector"] for c in chunks])
    question = np.array(question_vector)

    # Cosine similarity = how closely two vectors point in the same direction.
    # Divide by the lengths so long and short texts are compared fairly.
    scores = matrix @ question / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(question) + 1e-10)

    best = np.argsort(scores)[::-1][:top_k]          # positions of the highest scores
    return [
        {"text": chunks[i]["text"], "source": chunks[i]["source"],
         "page": chunks[i]["page"], "score": round(float(scores[i]), 2)}
        for i in best
    ]


def status():
    """Return (number_of_chunks, built_at), or (0, None) if not built yet."""
    data = load()
    if not data:
        return 0, None
    return len(data["chunks"]), data["built_at"]


def sources():
    """Names of all documents in the knowledge base."""
    data = load()
    return sorted({c["source"] for c in data["chunks"]}) if data else []
