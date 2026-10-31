from pathlib import Path
from pypdf import PdfReader

pdf_files = sorted(Path("data").glob("*.pdf"))

if not pdf_files:
    print("No PDF files found in the data folder.")
else:
    total_pages = 0
    print(f"Found {len(pdf_files)} PDF files:\n")
    for file in pdf_files:
        reader = PdfReader(file)
        pages = len(reader.pages)
        total_pages += pages
        check_page = reader.pages[min(2, pages - 1)]
        text = check_page.extract_text() or ""
        status = "OK - text readable" if len(text) > 200 else "WARNING - may be scanned, replace it"
        print(f"{file.name:40} {pages:4} pages   {status}")
    print(f"\nTotal pages: {total_pages}")