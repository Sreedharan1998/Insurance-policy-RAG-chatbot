import csv
import time

import rag

# (question, type, expected source keywords)
TESTS = [
    # ---- should be answerable from the documents ----
    ("What is the waiting period for pre-existing diseases?", "answer", ["star_health"]),
    ("What is the free look period?", "answer", ["hdfc", "star_health"]),
    ("Which documents are needed to make a claim?", "answer", ["hdfc", "star_health"]),
    ("What is the grace period for premium payment?", "answer", ["hdfc"]),
    ("Is intentional self-injury covered?", "answer", ["star_health"]),
    ("What are the exclusions under the Star Health Assure policy?", "answer", ["star_health"]),
    ("What is the death benefit under the HDFC Click 2 Protect term plan?", "answer", ["click2protect"]),
    ("Which critical illnesses are covered?", "answer", ["hdfc"]),
    ("What is the waiting period for listed conditions like cataract or hernia?", "answer", ["star_health"]),
    ("What does the policy say about hospitalization expenses?", "answer", ["star_health", "easy_protect"]),
    # ---- out of scope: the bot should refuse ----
    ("What is the capital of France?", "refuse", []),
    ("Who won the cricket world cup?", "refuse", []),
    ("Write a Python program to sort a list.", "refuse", []),
    ("What is the exact premium for a 35 year old non-smoker?", "refuse", []),
    ("Which insurance company is the best in India?", "refuse", []),
]

REFUSAL = "could not find"
rows = []
answer_ok = 0
refuse_ok = 0

for i, (question, kind, expected) in enumerate(TESTS, start=1):
    result = rag.ask(question)
    answer = result["answer"].replace("\n", " ")
    sources = [f"{s['source']} p{s['page']}" for s in result["sources"]]
    refused = answer.lower().startswith("i could not find")
    busy = answer.startswith("Sorry, the AI service")

    if busy:
        status = "ERROR (AI busy, run again)"
    elif kind == "refuse":
        status = "PASS" if refused else "FAIL (answered an out-of-scope question)"
        refuse_ok += status == "PASS"
    else:
        source_match = any(
            e in s["source"] for s in result["sources"] for e in expected
        )
        if refused:
            status = "NOT FOUND (retrieval problem?)"
        elif source_match:
            status = "ANSWERED (verify by hand)"
            answer_ok += 1
        else:
            status = "ANSWERED, UNEXPECTED SOURCE (verify)"

    print(f"\n{i:2}. {question}")
    print(f"    {status}")
    print(f"    {answer[:160]}...")

    rows.append([i, question, kind, status, answer, "; ".join(sources), ""])
    time.sleep(3)   # be kind to the free API limit

with open("eval_results.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["No", "Question", "Type", "Auto status", "Answer", "Sources", "My check (correct / wrong)"])
    writer.writerows(rows)

print("\n" + "=" * 60)
print(f"Answerable questions answered : {answer_ok} / 10")
print(f"Out-of-scope questions refused: {refuse_ok} / 5")
print("Saved to eval_results.csv")