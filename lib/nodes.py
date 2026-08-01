import json
import os
import dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from lib.response_schemas import ExtractionSchema, IntentSchema
from lib.state import AgentState
from lib.store import vectorstore

from rapidfuzz import process, fuzz

PDF_DIR = "data/qp_pdfs"
CHROMA_DIR = "chroma_db"
METADATA_PATH = "data/pdf_metadata.json"

dotenv.load_dotenv()

pdf_metadata = json.load(open(METADATA_PATH)) if os.path.exists(METADATA_PATH) else []

llm_main = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
llm_groq = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

intent_chain = llm_groq.with_structured_output(IntentSchema)
extractor_chain = llm_groq.with_structured_output(ExtractionSchema)


# Sometimes gemini outputs as a list
def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "".join(parts)
    return str(content)

def classify_intent_node(state: AgentState) -> dict:
    result: IntentSchema = intent_chain.invoke(state["query"])
    return {"intent": result.intent}


def extract_parameters_node(state: AgentState) -> dict:
    result = extractor_chain.invoke(
        f"Extract the subject and sessions from this query: {state['query']}"
    )
    return {
        "extracted_subject": result.subject,
        "extracted_sessions": result.sessions
    }


def fetch_pdfs_node(state: AgentState) -> dict:
    subject_keyword = (state.get("extracted_subject") or "").lower().replace(" ", "").replace("-", "")
    target_sessions = [s.lower().replace(" ", "") for s in state["extracted_sessions"]]
    found_files = []

    for entry in pdf_metadata:
        code = entry.get("course_code", "").lower().replace(" ", "").replace("-", "")
        name = entry.get("course_name", "").lower().replace(" ", "")
        session = entry.get("session", "").lower().replace(" ", "").replace(",", "")

        subject_match = subject_keyword in code or subject_keyword in name
        session_match = any(s in session for s in target_sessions)

        if subject_match and session_match:
            found_files.append(entry["pdf_path"])

    if not found_files and subject_keyword:
        names = [e.get("course_name", "") for e in pdf_metadata]
        match = process.extractOne(subject_keyword, names, scorer=fuzz.WRatio)
        if match and match[1] >= 70:
            found_files = [pdf_metadata[match[2]]["pdf_path"]]

    if found_files:
        sessions_str = ", ".join(state["extracted_sessions"])
        response = f"I found {len(found_files)} paper(s) for {state['extracted_subject']} ({sessions_str}). I'm displaying them for you now."
    else:
        response = f"I couldn't find any papers for '{state['extracted_subject']}' in the requested sessions. Try specifying the exact course code."

    return {"found_pdfs": found_files, "final_response": response}


def general_doubt_node(state: AgentState) -> dict:
    docs = vectorstore.similarity_search(state["query"], k=3)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = (
        "You are an experienced assistant for IGNOU website.",
        "Provide only the answer to the question using only the context below.",
        "Do not prefix the answer with 'according to the context' or any similar phrase.",
        "Ensure the answer is detailed, complete and directly addresses the question.",
        "Throughout the query any references to colleges or universities is to IGNOU",
        "doesn't contain the answer, say you don't have that information.\n\n",
        f"Context:\n{context}\n\nQuestion: {state['query']}"
    )
    resp = llm_main.invoke(prompt)
    return {"found_pdfs": [], "final_response": extract_text(resp.content)}
