from rag import ask

def show(question):
    result = ask(question)
    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("\nANSWER:\n" + result["answer"])
    print("\nSOURCES USED:")
    print("\nMODEL USED:", result.get("model"))
    for s in result["sources"]:
        print(f"  - {s['source']} | page {s['page']} | distance {s['distance']}")

# 1. Two automatic questions
show("What is the waiting period for pre-existing diseases?")
show("What is the free look period?")

# 2. Then ask your own questions
print("\n\nNow ask your own questions. Type exit to stop.")
while True:
    q = input("\nYour question: ").strip()
    if q.lower() in ("exit", "quit", ""):
        break
    show(q)

    