import json
import time
import unicodedata

import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

from config import get_key

LLM_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.8-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]
TOP_K = 8

SYSTEM_RULES = """You are an insurance policy assistant.
Rules:
1. Answer using ONLY the CONTEXT given below. Do not use outside knowledge.
2. If the CONTEXT has related information, summarize what it says, even if it is only partial, and clearly say what is missing.
3. Reply exactly: "I could not find this in the policy documents." only when the CONTEXT has nothing relevant to the question.
4. Use simple, short English.
5. Say which policy document (file name) the information comes from. Never write "Source 1" or "Source 2".
6. Do not give legal or financial advice."""

_embedder = None
_collection = None
_llm = None


def _build_db(db):
    """Create the vector database from chunks.json (used when chroma_db is missing)."""
    with open("chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    for c in chunks:
        c["text"] = unicodedata.normalize("NFKC", c["text"])

    texts = [c["text"] for c in chunks]
    embeddings = _embedder.encode(texts, batch_size=32, normalize_embeddings=True)

    collection = db.create_collection(
        name="policies", metadata={"hnsw:space": "cosine"}
    )
    BATCH = 200
    for i in range(0, len(chunks), BATCH):
        part = chunks[i:i + BATCH]
        collection.add(
            ids=[str(c["id"]) for c in part],
            documents=[c["text"] for c in part],
            metadatas=[{"source": c["source"], "page": c["page"]} for c in part],
            embeddings=embeddings[i:i + BATCH].tolist(),
        )
    return collection


def _load():
    """Load the models once and reuse them."""
    global _embedder, _collection, _llm
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        db = chromadb.PersistentClient(path="chroma_db")
        try:
            _collection = db.get_collection("policies")
            if _collection.count() == 0:
                raise ValueError("empty collection")
        except Exception:
            try:
                db.delete_collection("policies")
            except Exception:
                pass
            _collection = _build_db(db)
        _llm = genai.Client(
            api_key=get_key(),
            http_options=types.HttpOptions(timeout=25000),
        )


def retrieve(question, k=TOP_K):
    """Find the k chunks most similar to the question."""
    _load()
    q_emb = _embedder.encode([question], normalize_embeddings=True).tolist()
    res = _collection.query(query_embeddings=q_emb, n_results=k)
    chunks = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        chunks.append(
            {
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "distance": round(dist, 2),
            }
        )
    return chunks


def build_prompt(question, chunks):
    context = ""
    for i, c in enumerate(chunks, start=1):
        context += f"[Source {i}: {c['source']}, page {c['page']}]\n{c['text']}\n\n"
    return f"CONTEXT:\n{context}\nQUESTION: {question}\n\nANSWER:"


def ask(question):
    """Main function: returns the answer, the sources and the model used."""
    chunks = retrieve(question)
    prompt = build_prompt(question, chunks)

    answer = None
    used_model = None
    last_error = None
    started = time.time()
    MAX_SECONDS = 75          # give up after 75 seconds in total

    for model_name in LLM_MODELS:
        if time.time() - started > MAX_SECONDS:
            break
        try:
            response = _llm.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_RULES, temperature=0.2
                ),
            )
            answer = response.text or "Sorry, I could not generate an answer."
            used_model = model_name
            break
        except Exception as e:
            last_error = e
            if "404" in str(e) or "NOT_FOUND" in str(e):
                continue          # model not available: try the next one
            time.sleep(2)         # busy or slow: short pause, next model

    if answer is None:
        answer = ("Sorry, the AI service is busy right now. "
                  f"Please try again in a minute. ({last_error})")
    return {"answer": answer, "sources": chunks, "model": used_model}