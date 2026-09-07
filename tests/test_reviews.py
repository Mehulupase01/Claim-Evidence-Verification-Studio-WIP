import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.dependencies import get_storage_service, get_verifier_service
from app.errors import VerifierError, VerifierTimeoutError
from app.main import app
from app.models import LLMDecision, Verdict
from app.services.storage import InMemoryStorage


class FakeVerifier:
    def __init__(self, decision: LLMDecision) -> None:
        self.decision = decision
        self.seen_evidence = []

    @property
    def model_identifier(self) -> str:
        return "fake/deterministic"

    async def verify(self, claim, evidence):
        self.seen_evidence = evidence
        return self.decision


class FailingVerifier(FakeVerifier):
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def verify(self, claim, evidence):
        raise self.error


async def client_for(storage, verifier, settings: Settings | None = None):
    app.dependency_overrides[get_storage_service] = lambda: storage
    app.dependency_overrides[get_verifier_service] = lambda: verifier
    app.dependency_overrides[get_settings] = lambda: settings or Settings(
        _env_file=None
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.parametrize(
    ("verdict", "evidence_ids"),
    [
        (Verdict.SUPPORTED, ["chunk_0001"]),
        (Verdict.CONTRADICTED, ["chunk_0001"]),
        (Verdict.INSUFFICIENT_EVIDENCE, []),
    ],
)
@pytest.mark.asyncio
async def test_upload_review_and_persisted_get_round_trip(verdict, evidence_ids) -> None:
    storage = InMemoryStorage()
    verifier = FakeVerifier(
        LLMDecision(
            verdict=verdict,
            reasoning="The source passage determines this result.",
            evidence_ids=evidence_ids,
        )
    )
    client = await client_for(storage, verifier)
    try:
        async with client:
            upload = await client.post(
                "/documents",
                files={
                    "file": (
                        "report.txt",
                        b"Revenue increased by 27 percent during the second quarter.",
                        "text/plain",
                    )
                },
            )
            assert upload.status_code == 201
            document_id = upload.json()["document_id"]

            created = await client.post(
                "/reviews",
                json={
                    "document_id": document_id,
                    "claim": "Revenue increased by 27 percent in Q2.",
                },
            )
            assert created.status_code == 201
            review = created.json()
            retrieved = await client.get(f"/reviews/{review['review_id']}")
    finally:
        app.dependency_overrides.clear()

    assert retrieved.status_code == 200
    assert retrieved.json() == review
    assert review["verdict"] == verdict.value
    assert review["model"] == "fake/deterministic"
    assert f"reviews/{review['review_id']}.json" in storage.objects
    if evidence_ids:
        assert review["evidence"][0]["text"].startswith("Revenue increased")
        assert review["evidence"][0]["page"] == 1
    else:
        assert review["evidence"] == []


@pytest.mark.asyncio
async def test_missing_document_and_review_return_specific_404s() -> None:
    storage = InMemoryStorage()
    verifier = FakeVerifier(
        LLMDecision(
            verdict=Verdict.INSUFFICIENT_EVIDENCE,
            reasoning="No evidence was supplied.",
            evidence_ids=[],
        )
    )
    client = await client_for(storage, verifier)
    try:
        async with client:
            missing_document = await client.post(
                "/reviews",
                json={
                    "document_id": "doc_" + "a" * 32,
                    "claim": "This claim is long enough.",
                },
            )
            missing_review = await client.get("/reviews/rev_" + "b" * 32)
    finally:
        app.dependency_overrides.clear()

    assert missing_document.status_code == 404
    assert missing_document.json()["error"]["code"] == "document_not_found"
    assert missing_review.status_code == 404
    assert missing_review.json()["error"]["code"] == "review_not_found"


@pytest.mark.asyncio
async def test_route_rejects_unknown_evidence_from_any_verifier() -> None:
    storage = InMemoryStorage()
    verifier = FakeVerifier(
        LLMDecision(
            verdict=Verdict.SUPPORTED,
            reasoning="This tries to use invented evidence.",
            evidence_ids=["chunk_9999"],
        )
    )
    client = await client_for(storage, verifier)
    try:
        async with client:
            upload = await client.post(
                "/documents",
                files={"file": ("report.txt", b"A sufficiently useful source passage for the test.", "text/plain")},
            )
            response = await client.post(
                "/reviews",
                json={
                    "document_id": upload.json()["document_id"],
                    "claim": "A sufficiently clear claim.",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_evidence_reference"
    assert not any(key.startswith("reviews/") for key in storage.objects)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (VerifierTimeoutError(), 504, "verifier_timeout"),
        (VerifierError(), 502, "verifier_unavailable"),
    ],
)
@pytest.mark.asyncio
async def test_verifier_failures_are_mapped_and_never_persisted(
    error, expected_status, expected_code
) -> None:
    storage = InMemoryStorage()
    verifier = FailingVerifier(error)
    client = await client_for(storage, verifier)
    try:
        async with client:
            upload = await client.post(
                "/documents",
                files={"file": ("report.txt", b"A sufficiently useful source passage for the test.", "text/plain")},
            )
            response = await client.post(
                "/reviews",
                json={
                    "document_id": upload.json()["document_id"],
                    "claim": "A sufficiently clear claim.",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    assert not any(key.startswith("reviews/") for key in storage.objects)


@pytest.mark.asyncio
async def test_corrupt_saved_review_returns_safe_502() -> None:
    storage = InMemoryStorage()
    review_id = "rev_" + "c" * 32
    storage.objects[f"reviews/{review_id}.json"] = json.dumps(
        {"review_id": review_id, "unexpected": "shape"}
    ).encode()
    verifier = FakeVerifier(
        LLMDecision(
            verdict=Verdict.INSUFFICIENT_EVIDENCE,
            reasoning="Unused.",
            evidence_ids=[],
        )
    )
    client = await client_for(storage, verifier)
    try:
        async with client:
            response = await client.get(f"/reviews/{review_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_stored_artifact"
