"""
llm.py  -  THE ONLY FILE THAT TALKS TO GEMINI
=============================================

Same idea as Project 1: every other file asks this one when it needs the AI.
This time it can do two jobs:

1. ask_ai()      - send a question, get written text back (like Project 1)
2. embed_texts() - turn text into EMBEDDINGS: lists of numbers that capture
                   meaning. Texts that mean similar things get similar numbers.
                   This is what lets us search documents by meaning.

Both jobs share the same safety net: if Google is busy, wait and retry.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Models for writing answers, tried in order (same as Project 1).
CHAT_MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
]

# The model that turns text into numbers. One model only, on purpose:
# documents and questions MUST be turned into numbers by the same model,
# or comparing them would be like comparing prices in AED and in USD.
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
EMBED_SIZE = 768          # how many numbers per text (768 is a good balance of quality and speed)
EMBED_BATCH = 100         # how many texts we send to Google in one request


class AIError(Exception):
    """A friendly error we show on screen instead of a crash."""


def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "paste-your-key-here":
        raise AIError(
            "No API key found. Open the .env file in this folder, paste your "
            "Gemini key after GEMINI_API_KEY=, save it, and restart the app."
        )
    return key


def what_went_wrong(message):
    """Sort Google's error message into a simple kind, so we know what to do."""
    if any(sign in message for sign in ("503", "UNAVAILABLE", "500", "INTERNAL", "overloaded")):
        return "busy"
    if "404" in message or "not found" in message.lower():
        return "missing"
    if "429" in message or "RESOURCE_EXHAUSTED" in message:
        return "limit"
    if "API key" in message or "API_KEY" in message:
        return "bad_key"
    return "other"


def explain(kind, problem):
    """Turn an error kind into a message a person can act on."""
    if kind == "limit":
        return ("Gemini's free tier limit was reached. Wait one minute and try again "
                "(or tomorrow, if you hit the daily limit).")
    if kind == "bad_key":
        return ("Gemini rejected your API key. Check it's pasted correctly in .env "
                "with no spaces or quotes, then restart the app.")
    if kind == "busy":
        return "Gemini is very busy right now. Wait a minute and try again."
    return f"Gemini returned an error: {problem}"


def with_retries(models, send_request):
    """
    The safety net used by both jobs.
    Tries each model up to 3 times when Google is busy (waiting 2s, then 4s),
    moves to the next model if one stays busy or doesn't exist,
    and stops with a clear message for anything else.
    `send_request` is a small function that does the actual call for one model.
    """
    last_problem, last_kind = None, "other"
    for model in [m for m in models if m]:
        for attempt in range(3):
            try:
                return send_request(model)
            except Exception as problem:
                last_problem, last_kind = problem, what_went_wrong(str(problem))
                if last_kind == "busy" and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                if last_kind in ("busy", "missing"):
                    break
                raise AIError(explain(last_kind, problem))
    raise AIError(explain(last_kind, last_problem))


def ask_ai(system_prompt, user_message, temperature=0.2):
    """Ask Gemini a question. Returns {"text", "input_tokens", "output_tokens", "model"}."""
    client = genai.Client(api_key=get_api_key())
    settings = types.GenerateContentConfig(system_instruction=system_prompt, temperature=temperature)

    def send(model):
        response = client.models.generate_content(model=model, contents=user_message, config=settings)
        usage = response.usage_metadata
        return {
            "text": response.text or "",
            "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
            "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
            "model": model,
        }

    return with_retries(CHAT_MODELS, send)


def embed_texts(texts, purpose):
    """
    Turn a list of texts into a list of embeddings (one list of numbers per text).
    purpose: "document" when storing pieces of our documents,
             "question" when turning a user's question into numbers.
    Google uses this hint to make questions and answers line up better.
    """
    client = genai.Client(api_key=get_api_key())
    task = "RETRIEVAL_DOCUMENT" if purpose == "document" else "RETRIEVAL_QUERY"
    settings = types.EmbedContentConfig(task_type=task, output_dimensionality=EMBED_SIZE)

    all_vectors = []
    for start in range(0, len(texts), EMBED_BATCH):          # send in batches of 100
        batch = texts[start:start + EMBED_BATCH]

        def send(model):
            result = client.models.embed_content(model=model, contents=batch, config=settings)
            return [e.values for e in result.embeddings]

        all_vectors.extend(with_retries([EMBED_MODEL], send))
    return all_vectors
