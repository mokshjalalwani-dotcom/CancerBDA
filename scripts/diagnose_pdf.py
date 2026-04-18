import pdfplumber
import io
from pathlib import Path
import re

pdf_path = 'sample_report.pdf'
if not Path(pdf_path).exists():
    print(f"File {pdf_path} not found")
    exit(1)

content = Path(pdf_path).read_bytes()
text = ""
with pdfplumber.open(io.BytesIO(content)) as pdf:
    for page in pdf.pages:
        text += page.extract_text() or ""

print("--- EXTRACTED TEXT ---")
print(text)
print("----------------------")

# Test Regex
print("\n--- REGEX TESTING ---")
stage_match = re.search(r"Stage\s+(I{1,3}|IV)", text, re.IGNORECASE)
print(f"Stage Match: {stage_match.group(1) if stage_match else 'None'}")

grade_match = re.search(r"Grade\s+(G[1-3])", text, re.IGNORECASE)
if not grade_match:
    grade_match = re.search(r"\b(G[1-3])\b", text, re.IGNORECASE)
print(f"Grade Match: {grade_match.group(1) if grade_match else 'None'}")

meta_match = re.search(r"Metastasis:\s*(Yes|No)", text, re.IGNORECASE)
print(f"Metastasis Match: {meta_match.group(1) if meta_match else 'None'}")

ensg_matches = list(re.finditer(r"(ENSG\d+\.\d+)[:\s]+([\d\.]+)", text))
print(f"ENSG Matches Found: {len(ensg_matches)}")
for m in ensg_matches[:5]:
    print(f"  {m.group(1)}: {m.group(2)}")
