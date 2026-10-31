import json
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

CHUNK_SIZE = 1000
OVERLAP = 150


def norm(line):
    """Replace numbers so 'Page 3' and 'Page 4' look the same."""
    return re.sub(r"\d+", "#", line.strip())


def clean_pages(raw_pages):
    """Remove header/footer lines that repeat on many pages."""
    counts = Counter()
    for text in raw_pages:
        lines = {norm(l) for l in text.splitlines() if l.strip()}
        counts.update(lines)

    limit = max(3, int(len(raw_pages) * 0.4))
    boiler = {l for l, c in counts.items() if c >= limit and len(l) > 10}

    cleaned = []
    for text in raw_pages:
        keep = [l for l in text.splitlines() if norm(l) not in boiler]
        cleaned.append(" ".join(" ".join(keep).split()))
    return cleaned, boiler


def split_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start + size // 2:
                end = space
        piece = text[start:end].strip()
        if len(piece) >= 80:
            chunks.append(piece)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


all_chunks = []

for file in sorted(Path("data").glob("*.pdf")):
    reader = PdfReader(file)
    raw_pages = [(p.extract_text() or "") for p in reader.pages]
    pages, boiler = clean_pages(raw_pages)

    before = len(all_chunks)
    for page_number, text in enumerate(pages, start=1):
        for piece in split_text(text):
            all_chunks.append(
                {
                    "id": len(all_chunks),
                    "source": file.name,
                    "page": page_number,
                    "text": piece,
                }
            )
    made = len(all_chunks) - before
    print(f"{file.name:38} {len(reader.pages):3} pages -> {made:4} chunks "
          f"({len(boiler)} repeated lines removed)")
    for b in list(boiler)[:2]:
        print("      removed:", b[:90])

with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print(f"\nTotal chunks: {len(all_chunks)}")
print("Saved to chunks.json")