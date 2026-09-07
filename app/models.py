from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Verdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class HealthResponse(StrictModel):
    status: str = "ok"


class EvidenceChunk(StrictModel):
    evidence_id: str = Field(pattern=r"^chunk_\d{4}$")
    page: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=5000)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_offsets(self) -> "EvidenceChunk":
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self


class ExtractedDocument(StrictModel):
    document_id: str = Field(pattern=r"^doc_[0-9a-f]{32}$")
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    page_count: int = Field(ge=1)
    chunks: list[EvidenceChunk] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)


class DocumentUploadResponse(StrictModel):
    document_id: str = Field(pattern=r"^doc_[0-9a-f]{32}$")
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    page_count: int = Field(ge=1)
    chunk_count: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utc_now)


class CreateReviewRequest(StrictModel):
    document_id: str = Field(pattern=r"^doc_[0-9a-f]{32}$")
    claim: str = Field(min_length=3, max_length=2000)


class RankedChunk(EvidenceChunk):
    retrieval_score: float = Field(ge=0)


class LLMDecision(StrictModel):
    verdict: Verdict
    reasoning: str = Field(min_length=1, max_length=800)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)


class Evidence(StrictModel):
    evidence_id: str = Field(pattern=r"^chunk_\d{4}$")
    page: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=5000)
    retrieval_score: float = Field(ge=0)


class ReviewResponse(StrictModel):
    review_id: str = Field(pattern=r"^rev_[0-9a-f]{32}$")
    document_id: str = Field(pattern=r"^doc_[0-9a-f]{32}$")
    claim: str = Field(min_length=3, max_length=2000)
    verdict: Verdict
    reasoning: str = Field(min_length=1, max_length=800)
    evidence: list[Evidence]
    model: str = Field(min_length=1, max_length=200)
    created_at: datetime = Field(default_factory=utc_now)
