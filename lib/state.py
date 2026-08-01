from typing import TypedDict


class AgentState(TypedDict):
    query: str
    intent: str | None
    extracted_subject: str | None
    extracted_sessions: list[str]
    found_pdfs: list[str]
    final_response: str