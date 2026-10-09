"""
ingest.py  -  BUILDS THE KNOWLEDGE BASE (run once, or whenever documents change)
================================================================================

Think of this as preparing an open-book exam:
1. READ every document in the "documents" folder (PDF, Markdown or text).
2. CUT the text into small overlapping pieces ("chunks") of about 120 words.
   Small pieces let us find exactly the right paragraph, not a whole 10-page PDF.
   Overlap means each piece repeats the last few lines of the one before it,
   so a sentence that sits on the border between two pieces isn't lost.
3. EMBED each chunk: turn it into a list of numbers that captures its meaning.
4. STORE chunks + numbers + "where it came from" in our own small vector
   database (vector_store.py), saved in the "brand_db" folder on your computer.
"""

from pathlib import Path

from pypdf import PdfReader

import vector_store
from llm import EMBED_MODEL, embed_texts

FOLDER = Path(__file__).parent
DOCUMENTS_FOLDER = FOLDER / "documents"
SUPPORTED = {".pdf", ".md", ".txt"}

# ---- CHUNK SETTINGS (try changing these and re-building to see the effect) ----
CHUNK_WORDS = 120        # words per chunk
OVERLAP_WORDS = 25       # words repeated from the previous chunk


def read_document(path):
    """
    Return a list of (page_number, text) for one file.
    PDFs are read page by page so we can later say "page 3".
    Markdown and text files count as one page.
    """
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return [(number, page.extract_text() or "") for number, page in enumerate(reader.pages, start=1)]
    return [(1, path.read_text(encoding="utf-8", errors="ignore"))]


def cut_into_chunks(text):
    """Slice text into ~120-word pieces, each overlapping the previous one by 25 words."""
    words = text.split()
    if not words:
        return []
    step = CHUNK_WORDS - OVERLAP_WORDS
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + CHUNK_WORDS]))
        if start + CHUNK_WORDS >= len(words):     # reached the end of the text
            break
    return chunks


def build_knowledge_base(report=print):
    """
    Read every document, chunk it, embed it, and save it to the vector store.
    Starts fresh each time, so deleted documents disappear from the bot too.
    `report` is how we send progress messages (print in a terminal, or the app's screen).
    Returns a small summary dictionary.
    """
    files = sorted(p for p in DOCUMENTS_FOLDER.iterdir() if p.suffix.lower() in SUPPORTED)
    if not files:
        raise ValueError("The documents folder is empty. Add PDF, .md or .txt files and try again.")

    chunks = []
    for path in files:
        pieces_in_file = 0
        for page, page_text in read_document(path):
            for number, text in enumerate(cut_into_chunks(page_text), start=1):
                chunks.append({"text": text, "source": path.name, "page": page, "chunk": number})
                pieces_in_file += 1
        report(f"Read {path.name}: {pieces_in_file} chunks")

    if not chunks:
        raise ValueError("No readable text was found. Scanned PDFs (photos of pages) can't be read yet.")

    report(f"Turning {len(chunks)} chunks into embeddings with {EMBED_MODEL}...")
    vectors = embed_texts([c["text"] for c in chunks], purpose="document")

    vector_store.save(chunks, vectors, EMBED_MODEL)     # replaces the old knowledge base
    report(f"Saved {len(chunks)} chunks from {len(files)} documents.")
    return {"documents": len(files), "chunks": len(chunks)}


def knowledge_base_status():
    """Return (number_of_chunks, built_at) or (0, None) if not built yet."""
    return vector_store.status()


if __name__ == "__main__":
    build_knowledge_base()
