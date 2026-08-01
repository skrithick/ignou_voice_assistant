import json
import os

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from lib.nodes import (
    classify_intent_node,
    extract_parameters_node,
    fetch_pdfs_node,
    general_doubt_node,
)
from lib.response_schemas import QueryResult
from lib.state import AgentState

load_dotenv()

PDF_DIR = "data/qp_pdfs"
CHROMA_DIR = "chroma_db"
METADATA_PATH = "data/pdf_metadata.json"

workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("extract", extract_parameters_node)
workflow.add_node("fetch_pdfs", fetch_pdfs_node)
workflow.add_node("general_doubt", general_doubt_node)

workflow.set_entry_point("classify_intent")
workflow.add_conditional_edges(
    "classify_intent",
    lambda state: state["intent"],
    {"fetch_paper": "extract", "general_doubt": "general_doubt"},
)
workflow.add_edge("extract", "fetch_pdfs")
workflow.add_edge("fetch_pdfs", END)
workflow.add_edge("general_doubt", END)

app = workflow.compile()


def query(user_query: str) -> QueryResult:
    final_state = app.invoke({"query": user_query})
    found_pdfs = final_state.get("found_pdfs", [])
    return QueryResult(
        exists=bool(found_pdfs),
        response=final_state["final_response"],
        pdf_paths=found_pdfs,
        intent=final_state.get("intent"),
    )


if __name__ == "__main__":
    test_queries = [
        "I want AEC question papers from 2024",
    ]

    for user_query in test_queries:
        result = query(user_query)
        print(result.model_dump_json(indent=2))