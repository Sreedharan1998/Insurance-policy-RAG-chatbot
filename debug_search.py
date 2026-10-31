import json
import rag

KEYWORDS = ["death benefit", "sum assured on death", "critical illness",
            "hospitalisation", "hospitalization", "free look"]

with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

print("PART 1: Does this text exist in the documents?")
for kw in KEYWORDS:
    hits = [c for c in chunks if kw in c["text"].lower()]
    print(f"\n'{kw}': found in {len(hits)} chunks")
    for c in hits[:3]:
        print(f"   - {c['source']} page {c['page']}")

QUESTIONS = [
    "What is the death benefit under the HDFC Click 2 Protect term plan?",
    "Which critical illnesses are covered?",
    "What does the policy say about hospitalization expenses?",
]

print("\n\nPART 2: What does the search return?")
for q in QUESTIONS:
    print("\n" + "=" * 70)
    print(q)
    for s in rag.retrieve(q):
        print(f"  [{s['source']} p{s['page']} d={s['distance']}] {s['text'][:150]}")