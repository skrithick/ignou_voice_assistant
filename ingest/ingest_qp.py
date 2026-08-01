import json
import os
import re

import pdfplumber
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()

PDF_DIR = "data/qp_pdfs"
OUTPUT_PATH = "data/pdf_metadata.json"

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def is_hindi_page(text: str) -> bool:
    devanagari_chars = len(DEVANAGARI_RE.findall(text))
    return devanagari_chars > 20 and devanagari_chars > len(text.strip()) * 0.3


class PdfMetadata(BaseModel):
    course_code: str = Field(description="Course code as printed, e.g. 'MCS-011'")
    course_name: str = Field(description="Full course/subject name as printed")
    exam_type: str = Field(description="Type of exam as printed, e.g. 'Term-End Examination'")
    session: str = Field(description="Session/date as printed, e.g. 'June, 2025'")


extractor_chain = llm.with_structured_output(PdfMetadata)


def get_first_page_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return "" if is_hindi_page(text) else text


def extract_metadata(pdf_path: str) -> dict:
    text = get_first_page_text(pdf_path)
    result = extractor_chain.invoke(
        f"Extract metadata from this question paper cover page:\n\n{text}"
    )
    return result.model_dump()


def build_all():
    os.makedirs(PDF_DIR, exist_ok=True)
    records = []

    for filename in sorted(os.listdir(PDF_DIR)):
        if not filename.endswith(".pdf"):
            continue
        path = os.path.join(PDF_DIR, filename)
        metadata = extract_metadata(path)
        metadata["filename"] = filename
        metadata["pdf_path"] = path
        records.append(metadata)
        print(f"{filename} -> {metadata}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_all()