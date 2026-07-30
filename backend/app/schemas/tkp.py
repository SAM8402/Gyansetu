from typing import Optional

from pydantic import BaseModel


class ValidationReport(BaseModel):
    """Validation report for a generated TKP (Teacher Knowledge Packet).

    The full TKP itself is represented as dynamic JSON — this schema
    covers only the validation / quality-assurance metadata.
    """

    schema_valid: bool
    completeness_score: float
    missing_elements: list[str]
    consistency_issues: list[str]
    hallucination_flags: list[str]
