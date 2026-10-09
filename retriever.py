"""
retriever.py  -  FINDS THE MOST RELEVANT PIECES FOR A QUESTION
==============================================================

This is the "R" in RAG: Retrieval.
1. Turn the user's question into numbers (an embedding), with the SAME model
   that was used for the documents.
2. Ask the vector store: "which saved chunks have numbers closest to these?"
   Close numbers = similar meaning, even if the words are different
   ("refund" finds a chunk that says "money back").
3. Return the best few chunks, with where each one came from.
"""

import vector_store
from llm import EMBED_MODEL, embed_texts

TOP_K = 4      # how many chunks to fetch for each question (try 2 or 6 and compare)


class NoKnowledgeBase(Exception):
    """Raised when someone asks a question before the documents were processed."""


def find_relevant_chunks(question, top_k=TOP_K, only_source=None):
    """
    Return a list of dictionaries, best match first:
        {"text": "...", "source": "faq.md", "page": 1, "score": 0.82}
    score: 1.0 = identical meaning, 0 = unrelated.
    only_source: optionally limit the search to one document, e.g. "customer_faq.md".
    """
    data = vector_store.load()
    if not data or not data["chunks"]:
        raise NoKnowledgeBase("The knowledge base isn't built yet. Click 'Build knowledge base' first.")
    if data["embed_model"] != EMBED_MODEL:
        raise NoKnowledgeBase(
            "The knowledge base was built with a different embedding model. "
            "Click 'Build knowledge base' to rebuild it."
        )

    question_vector = embed_texts([question], purpose="question")[0]
    return vector_store.search(question_vector, top_k=top_k, only_source=only_source)


def list_sources():
    """Names of all documents in the knowledge base (for the filter dropdown)."""
    return vector_store.sources()
