import json
import time
import unicodedata

import chromadb
from sentence_transformers import SentenceTransformer

# 1. Load the chunks from Step 3
with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

# fix special characters like the "fi" ligature (deﬁciency -> deficiency)
for c in chunks:
    c["text"] = unicodedata.normalize("NFKC", c["text"])

print(f"Loaded {len(chunks)} chunks")

# 2. Load the embedding model (first run downloads about 90 MB)
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Create embeddings
start = time.time()
texts = [c["text"] for c in chunks]
embeddings = model.encode(
    texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True
)
print(f"Created {len(embeddings)} embeddings in {time.time() - start:.0f} seconds")
print(f"Each embedding has {len(embeddings[0])} numbers")

# 4. Store everything in Chroma
client = chromadb.PersistentClient(path="chroma_db")
try:
    client.delete_collection("policies")   # so you can re-run safely
except Exception:
    pass
collection = client.create_collection(
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

print(f"\nStored {collection.count()} chunks in the Chroma database")

# 5. Test searches
questions = [
    "What is the waiting period for pre-existing diseases?",
    "What is the free look period?",
    "Which documents are needed to make a claim?",
]

for q in questions:
    print("\n" + "=" * 70)
    print("QUESTION:", q)
    q_emb = model.encode([q], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=3)
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        print(f"\n  [{meta['source']} | page {meta['page']} | distance {dist:.2f}]")
        print("  ", doc[:220], "...")