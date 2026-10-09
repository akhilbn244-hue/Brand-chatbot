"""
app.py  -  THE SCREEN YOU SEE
=============================

Left sidebar:  manage the knowledge base (see documents, add new ones, build it)
Tab 1 "Ask":   chat with the bot; every answer shows the sources it used
Tab 2 "Test":  run the 10-question test and get a score
"""

from pathlib import Path

import streamlit as st

from answer import answer_question
from evaluate import run_evaluation
from ingest import DOCUMENTS_FOLDER, SUPPORTED, build_knowledge_base, knowledge_base_status
from llm import AIError, get_api_key
from retriever import TOP_K, NoKnowledgeBase, list_sources

st.set_page_config(page_title="Brand Knowledge Chatbot", page_icon="📚", layout="wide")
st.title("Brand Knowledge Chatbot")
st.caption("Ask questions about the brand. Answers come only from your documents, with sources.")

# Everything needs the API key, so check it first.
try:
    get_api_key()
except AIError as problem:
    st.error(str(problem))
    st.stop()

# ================================================================ SIDEBAR
with st.sidebar:
    st.header("Knowledge base")

    chunk_count, built_at = knowledge_base_status()
    if chunk_count:
        st.success(f"Ready: {chunk_count} chunks · built {built_at}")
    else:
        st.warning("Not built yet. Click the button below.")

    documents = sorted(p.name for p in DOCUMENTS_FOLDER.iterdir() if p.suffix.lower() in SUPPORTED)
    st.markdown("**Documents in the folder**")
    for name in documents:
        st.markdown(f"- {name}")

    new_files = st.file_uploader("Add documents (PDF, .md, .txt)", type=["pdf", "md", "txt"],
                                 accept_multiple_files=True)
    if new_files and st.button("Save to documents folder"):
        for f in new_files:
            (DOCUMENTS_FOLDER / Path(f.name).name).write_bytes(f.getvalue())
        st.info("Saved. Now click 'Build knowledge base' so the bot can use them.")
        st.rerun()

    if st.button("Build knowledge base", type="primary"):
        with st.status("Building...", expanded=True) as status:
            try:
                summary = build_knowledge_base(report=st.write)
                status.update(label=f"Done: {summary['chunks']} chunks from {summary['documents']} documents",
                              state="complete")
            except (AIError, ValueError) as problem:
                status.update(label="Build failed", state="error")
                st.error(str(problem))
        st.rerun()

    st.divider()
    st.header("Search settings")
    top_k = st.slider("Chunks to retrieve per question", 1, 8, TOP_K,
                      help="More chunks = more context for the AI, but more noise and more tokens.")
    sources = ["All documents"] + list_sources()
    chosen = st.selectbox("Search in", sources)
    only_source = None if chosen == "All documents" else chosen

# ================================================================ TABS
ask_tab, test_tab = st.tabs(["Ask the Marketing Brain", "Test the bot"])

with ask_tab:
    if "chat" not in st.session_state:
        st.session_state["chat"] = []          # list of {"role", "content", "sources"}

    st.markdown("Try: *What's our returns policy?* · *Which campaign did best in 2025?* · "
                "*How should we write to VIP customers?* · *Who is our CEO?* (it should say it doesn't know)")

    # Show the conversation so far.
    for message in st.session_state["chat"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander(f"Sources used ({len(message['sources'])})"):
                    for number, s in enumerate(message["sources"], start=1):
                        st.markdown(f"**[{number}] {s['source']}, page {s['page']}** · similarity {s['score']}")
                        st.caption(s["text"][:500] + ("..." if len(s["text"]) > 500 else ""))

    question = st.chat_input("Ask about products, policies, campaigns or brand voice...")
    if question:
        st.session_state["chat"].append({"role": "user", "content": question})
        try:
            with st.spinner("Searching the documents..."):
                result = answer_question(question, top_k=top_k, only_source=only_source)
            st.session_state["chat"].append(
                {"role": "assistant", "content": result["answer"], "sources": result["sources"]}
            )
        except (AIError, NoKnowledgeBase) as problem:
            st.session_state["chat"].append({"role": "assistant", "content": f"⚠️ {problem}"})
        st.rerun()

    if st.session_state["chat"] and st.button("Clear chat"):
        st.session_state["chat"] = []
        st.rerun()

with test_tab:
    st.markdown(
        "Asks the 10 questions in **eval_questions.csv**. Eight have answers in the documents; "
        "two don't, and the bot only passes those if it says it doesn't know. Takes about a minute."
    )
    if st.button("Run the 10-question test"):
        progress = st.empty()
        try:
            score, table = run_evaluation(report=lambda text: progress.info(text))
            progress.empty()
            st.metric("Score", f"{score}/{len(table)}")
            st.dataframe(table, width="stretch", hide_index=True)
            st.caption("Put this score in your README. Recruiters like a number more than 'it works'.")
        except (AIError, NoKnowledgeBase) as problem:
            progress.empty()
            st.error(str(problem))
