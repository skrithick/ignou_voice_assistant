import os
import re
import json
from typing import Optional
import pdfplumber

PDF_DIR = "data/qp_pdfs"
OUTPUT_PATH = "data/pdf_metadata.json"

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def is_hindi_page(text: str) -> bool:
    devanagari_chars = len(DEVANAGARI_RE.findall(text))
    return devanagari_chars > 20 and devanagari_chars > len(text.strip()) * 0.3


CODE_RE = re.compile(r"\b([A-Z]{2,6}[-\u2013\u2014]\d{1,4})\b")

SESSION_TOKENS = {
    "june2025": "June2025",
    "dec2025": "Dec2025",
    "december2025": "Dec2025",
    "dec2024": "Dec2024",
    "december2024": "Dec2024",
}

EXAM_TYPES = ["Term-End Examination", "Term End Examination", "Entrance Examination", "Assignment"]


def extract_metadata_regex(text: str) -> Optional[dict]:
    code_match = CODE_RE.search(text)
    if not code_match:
        return None
    raw_code = code_match.group(1)
    course_code = raw_code.replace("\u2013", "-").replace("\u2014", "-")

    course_name = ""
    line_match = re.search(re.escape(raw_code) + r"\s*[:\-\u2013\u2014]\s*(.+)", text)
    if line_match:
        course_name = line_match.group(1).strip().splitlines()[0]

    exam_type = ""
    for et in EXAM_TYPES:
        if et.lower() in text.lower():
            exam_type = et
            break

    clean = text.lower().replace(" ", "").replace(",", "")
    session = ""
    for token, label in SESSION_TOKENS.items():
        if token in clean:
            session = label
            break

    if not session or not course_name:
        return None

    return {
        "course_code": course_code,
        "course_name": course_name,
        "exam_type": exam_type,
        "session": session,
    }


def get_first_page_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return "" if is_hindi_page(text) else text


def build_all():
    os.makedirs(PDF_DIR, exist_ok=True)
    records = json.load(open(OUTPUT_PATH)) if os.path.exists(OUTPUT_PATH) else []
    done = {r["filename"] for r in records}
    skipped = []

    for filename in sorted(os.listdir(PDF_DIR)):
        if not filename.endswith(".pdf") or filename in done:
            continue

        path = os.path.join(PDF_DIR, filename)
        text = get_first_page_text(path)
        metadata = extract_metadata_regex(text)

        if metadata is None:
            skipped.append(filename)
            continue

        metadata["filename"] = filename
        metadata["pdf_path"] = path
        records.append(metadata)

        with open(OUTPUT_PATH, "w") as f:
            json.dump(records, f, indent=2)

        print(f"{filename} -> {metadata}")

    print(f"{len(records)} records total in {OUTPUT_PATH}")
    if skipped:
        print(f"{len(skipped)} PDFs skipped, regex found nothing:")
        for f in skipped:
            print(f" - {f}")


if __name__ == "__main__":
    build_all()