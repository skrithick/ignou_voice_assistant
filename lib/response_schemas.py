from typing import Literal

from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    exists: bool
    response: str
    pdf_paths: list[str] = []
    intent: str | None = None

class IntentSchema(BaseModel):
    intent: Literal["fetch_paper", "general_doubt"] = Field(
        description=(
            "fetch_paper: the user wants to see/retrieve a specific question paper. "
            "general_doubt: any other question about the university."
        )
    )

class ExtractionSchema(BaseModel):
    subject: str = Field(description="The core subject name or course code (e.g., 'Operating Systems' or 'MCS-011')")
    sessions: list[str] = Field(description="List of sessions. ONLY use these exact values: 'June2025', 'Dec2025', 'Dec2024'. If the user does not specify a year, return all three.")