import json
import logging
import uuid

from fastapi import APIRouter, Depends, status
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.dependencies import (
    get_retrieval_service,
    get_storage_service,
    get_verifier_service,
)
from app.errors import (
    DocumentNotFoundError,
    GroundingError,
    ObjectNotFoundError,
    ReviewNotFoundError,
    StoredArtifactError,
)
from app.models import (
    CreateReviewRequest,
    Evidence,
    ExtractedDocument,
    LLMDecision,
    RankedChunk,
    ReviewResponse,
)
from app.services.retrieval import RetrievalService
from app.services.storage import StorageService
from app.services.verifier import LLMVerifier


router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger("claim_verifier.reviews")


def extracted_key(document_id: str) -> str:
    return f"documents/{document_id}/extracted.json"


def review_key(review_id: str) -> str:
    return f"reviews/{review_id}.json"


def parse_extracted_artifact(data: bytes, document_id: str) -> ExtractedDocument:
    try:
        artifact = ExtractedDocument.model_validate_json(data)
    except ValidationError:
        raise StoredArtifactError() from None
    if artifact.document_id != document_id:
        raise StoredArtifactError()
    return artifact


def resolve_evidence(
    decision: LLMDecision, candidates: list[RankedChunk]
) -> list[Evidence]:
    by_id = {candidate.evidence_id: candidate for candidate in candidates}
    if len(decision.evidence_ids) != len(set(decision.evidence_ids)):
        raise GroundingError()
    if not set(decision.evidence_ids).issubset(by_id):
        raise GroundingError()
    return [
        Evidence(
            evidence_id=by_id[evidence_id].evidence_id,
            page=by_id[evidence_id].page,
            text=by_id[evidence_id].text,
            retrieval_score=by_id[evidence_id].retrieval_score,
        )
        for evidence_id in decision.evidence_ids
    ]


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    request: CreateReviewRequest,
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage_service),
    retriever: RetrievalService = Depends(get_retrieval_service),
    verifier: LLMVerifier = Depends(get_verifier_service),
) -> ReviewResponse:
    try:
        artifact_data = await storage.get_bytes(extracted_key(request.document_id))
    except ObjectNotFoundError:
        raise DocumentNotFoundError() from None

    artifact = parse_extracted_artifact(artifact_data, request.document_id)
    candidates = retriever.retrieve(
        request.claim, artifact.chunks, top_k=settings.retrieval_top_k
    )
    decision = await verifier.verify(request.claim, candidates)
    evidence = resolve_evidence(decision, candidates)

    review = ReviewResponse(
        review_id=f"rev_{uuid.uuid4().hex}",
        document_id=request.document_id,
        claim=request.claim,
        verdict=decision.verdict,
        reasoning=decision.reasoning,
        evidence=evidence,
        model=verifier.model_identifier,
    )
    await storage.put_bytes(
        review_key(review.review_id),
        json.dumps(review.model_dump(mode="json"), separators=(",", ":")).encode(
            "utf-8"
        ),
        content_type="application/json",
        metadata={
            "review-id": review.review_id,
            "document-id": review.document_id,
        },
    )
    logger.info(
        "review persisted",
        extra={
            "operation": "persist_review",
            "document_id": review.document_id,
            "review_id": review.review_id,
        },
    )
    return review


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> ReviewResponse:
    if not review_id.startswith("rev_") or len(review_id) != 36:
        raise ReviewNotFoundError()
    try:
        data = await storage.get_bytes(review_key(review_id))
    except ObjectNotFoundError:
        raise ReviewNotFoundError() from None
    try:
        review = ReviewResponse.model_validate_json(data)
    except ValidationError:
        raise StoredArtifactError() from None
    if review.review_id != review_id:
        raise StoredArtifactError()
    return review
