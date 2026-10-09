"""
answer.py  -  WRITES THE ANSWER, USING ONLY THE FOUND PIECES
============================================================

This is the "AG" in RAG: Augmented Generation.
We paste the chunks that retriever.py found into the prompt, number them
[1], [2], [3]..., and give Gemini strict rules:
- answer ONLY from these numbered sources,
- cite the source number after every fact,
- if the answer isn't there, say a fixed "I don't know" sentence instead of guessing.

That last rule is what stops the AI from "hallucinating" (making things up).
"""

from llm import ask_ai
from retriever import TOP_K, find_relevant_chunks

NOT_FOUND = "I don't know based on the brand documents."

SYSTEM_PROMPT = f"""You are the internal knowledge assistant for the brand Noor Fashion.
You help the marketing team answer questions using ONLY the numbered sources you are given.

Rules:
1. Use only facts that appear in the sources. Never use outside knowledge.
2. After every fact, cite its source number in square brackets, like [1] or [2][3].
3. If the sources do not contain the answer, reply with exactly: {NOT_FOUND}
4. Be concise: 1 to 4 sentences, or a short bullet list if the question asks for a list."""


def build_prompt(question, chunks):
    """Put the numbered sources and the question together into one message."""
    sources = "\n\n".join(
        f"[{number}] (from {c['source']}, page {c['page']})\n{c['text']}"
        for number, c in enumerate(chunks, start=1)
    )
    return f"SOURCES:\n{sources}\n\nQUESTION: {question}"


def answer_question(question, top_k=TOP_K, only_source=None):
    """
    The full RAG loop for one question.
    Returns {"answer": "...", "sources": [chunks], "found": True/False, "tokens": n, "model": "..."}
    """
    chunks = find_relevant_chunks(question, top_k=top_k, only_source=only_source)
    result = ask_ai(SYSTEM_PROMPT, build_prompt(question, chunks), temperature=0.1)
    answer = result["text"].strip()
    return {
        "answer": answer,
        "sources": chunks,
        "found": NOT_FOUND.lower() not in answer.lower(),
        "tokens": result["input_tokens"] + result["output_tokens"],
        "model": result["model"],
    }
