from pathlib import Path

import streamlit as st
from pypdf import PdfReader

import rag

st.set_page_config(
    page_title="Insurance Policy Assistant",
    page_icon="🛡️",
    layout="centered",
)

st.markdown(
    """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
    padding: 1.3rem 1.6rem;
    border-radius: 14px;
    margin-bottom: 1rem;
}
.hero h1 {margin: 0; font-size: 1.8rem; color: white; padding: 0;}
.hero p {margin: 0.3rem 0 0 0; color: white; opacity: 0.9;}
</style>
""",
    unsafe_allow_html=True,
)

SAMPLE_QUESTIONS = [
    "What is the waiting period for pre-existing diseases?",
    "Which documents are needed to make a claim?",
    "Can you share the details about hospitalization?",
    "What is the grace period for premium payment?",
]


@st.cache_resource(show_spinner="Loading AI models (first time only)...")
def warm_up():
    rag._load()
    return True


@st.cache_data
def doc_info():
    items = []
    for f in sorted(Path("data").glob("*.pdf")):
        try:
            items.append((f.name, len(PdfReader(f).pages)))
        except Exception:
            items.append((f.name, 0))
    return items


def set_pending(q):
    st.session_state.pending = q


def show_sources(sources):
    with st.expander(f"📄 Sources ({len(sources)})"):
        for s in sources:
            st.markdown(f"**{s['source']}** · page {s['page']} · distance {s['distance']}")
            st.caption(s["text"][:500] + "...")
            st.divider()


warm_up()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# ---------- header ----------
st.markdown(
    """
<div class="hero">
  <h1>🛡️ Insurance Policy Assistant</h1>
  <p>Ask questions about your policy documents. Answers come only from the documents, with sources.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- get the question (typed or clicked) ----------
question = st.chat_input("Ask a question about the policies...")
if st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None

# ---------- welcome screen with sample questions ----------
if not st.session_state.messages and not question:
    st.markdown("#### 👋 Try one of these questions")
    cols = st.columns(2)
    for i, q in enumerate(SAMPLE_QUESTIONS):
        cols[i % 2].button(
            q,
            key=f"sample_{i}",
            on_click=set_pending,
            args=(q,),
            use_container_width=True,
        )

# ---------- earlier messages ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])
        if msg.get("model"):
            st.caption(f"Answered by {msg['model']}")

# ---------- new question ----------
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the policies and thinking..."):
            result = rag.ask(question)
        st.markdown(result["answer"])
        show_sources(result["sources"])
        if result.get("model"):
            st.caption(f"Answered by {result['model']}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "model": result.get("model"),
        }
    )

# ---------- sidebar (drawn last so the counter is up to date) ----------
n_questions = sum(1 for m in st.session_state.messages if m["role"] == "user")

with st.sidebar:
    st.header("📚 Loaded documents")
    for name, pages in doc_info():
        st.markdown(f"📄 **{name}**  \n{pages} pages")

    st.divider()
    st.subheader("How it works")
    st.markdown(
        "1. Your question is turned into numbers (an embedding)\n"
        "2. The 5 most similar policy chunks are found in ChromaDB\n"
        "3. Gemini answers using only those chunks\n"
        "4. Sources are shown so you can verify the answer"
    )

    st.divider()
    st.metric("Questions asked", n_questions)
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Demo project. Not insurance advice.")