# Brand Knowledge Chatbot (RAG)

Retrieval-augmented chatbot over brand documents using Gemini embeddings and a vector store built from scratch, with source citations and an evaluation score.

![App screenshot](screenshot.png)

**Evaluation score:** _X/10 — run the "Test the bot" tab and put your score here._

## How it works

**Building the knowledge base (once):**

1. Reads every PDF, Markdown and text file in `documents/`.
2. Cuts the text into overlapping chunks of about 120 words.
3. Turns each chunk into an embedding (768 numbers that capture its meaning) with `gemini-embedding-001`.
4. Stores chunks, embeddings and their source (file and page) in a small **vector store I built myself** (`vector_store.py`), saved as one file.

**Answering a question:**

1. The question is embedded with the same model.
2. The vector store compares it with every chunk using **cosine similarity** (numpy) and returns the 4 closest in meaning.
3. Those chunks are numbered and pasted into the prompt, with strict rules: use only these sources, cite them, and say *"I don't know based on the brand documents"* if the answer isn't there.
4. Gemini answers; the app shows the answer and the sources it used.

**Evaluation:** 10 test questions with known answers, including 2 that are *not* in the documents. The bot only passes those if it refuses to guess.

## Tech used

Python · Gemini API (chat + embeddings) · numpy (vector search) · Streamlit · pypdf · pandas

## Project structure

| File | Job |
| --- | --- |
| `app.py` | The screen: knowledge-base sidebar, chat tab, test tab |
| `ingest.py` | Reads, chunks, embeds and stores the documents |
| `vector_store.py` | My own small vector database: saves embeddings, searches by cosine similarity |
| `retriever.py` | Finds the most relevant chunks for a question |
| `answer.py` | Builds the grounded prompt and gets a cited answer |
| `evaluate.py` | Scores the bot on `eval_questions.csv` |
| `llm.py` | The only file that talks to Gemini, with retry and fallback |
| `documents/` | Four sample documents for a fictional brand, Noor Fashion |

## How to run it (Windows)

1. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).
2. Double-click `setup.bat`. When Notepad opens, paste your key after `GEMINI_API_KEY=`, save, close.
3. Double-click `run.bat`. In the app, click **Build knowledge base**, then ask a question.

## What I learned

- _Write 3 bullets in your own words after the walkthrough._

## Why a custom vector store?

I first used Chroma, but its compiled components wouldn't load on my Windows machine. For a few hundred chunks, a hand-written cosine-similarity search is just as accurate, has no extra dependencies, and showed me exactly how vector search works. For millions of chunks I would switch to a dedicated vector database such as Chroma, Pinecone or pgvector.

## What I'd build next

- Hybrid search: combine meaning-based search with exact keyword search for product codes and prices
- A re-ranking step that double-checks which retrieved chunks really answer the question
- Read scanned PDFs with OCR
