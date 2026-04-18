import pdfplumber
import io
import re
from pathlib import Path

def diagnose(filename):
    print(f"\n=== DIAGNOSING {filename} ===")
    if not Path(filename).exists():
        print("FILE NOT FOUND")
        return

    content = Path(filename).read_bytes()
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    print("RAW TEXT START")
    print(text)
    print("RAW TEXT END")

    patterns = {
        "Stage": r"Stage[:-\s]+(I{1,3}|IV)",
        "Grade": r"Grade[:-\s]+(G[1-3])",
        "Grade_Alt": r"\b(G[1-3])\b",
        "Metastasis": r"Metastasis[:-\s]+(Yes|No)",
        "ENSG": r"(ENSG\d+(?:\.\d+)?)[:-\s]+([\d\.]+)"
    }

    print("\nMATCH RESULTS:")
    for name, pat in patterns.items():
        match = re.search(pat, text, re.IGNORECASE)
        print(f"{name}: {'MATCHED (' + str(match.group(0)) + ')' if match else 'FAIL'}")

diagnose("sample_report.pdf")
diagnose("test_report.pdf")
