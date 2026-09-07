from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app
from app.models import CreateReviewRequest, ReviewResponse, Verdict


@pytest.mark.asyncio
async def test_health_returns_typed_response_and_request_id() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/health", headers={"X-Request-ID": "test-request-1"}
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "test-request-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_invalid_inbound_request_id_is_replaced() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/health", headers={"X-Request-ID": "unsafe value!"}
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "unsafe value!"
    assert len(response.headers["X-Request-ID"]) == 32


def test_create_review_request_rejects_short_claim_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CreateReviewRequest(document_id="doc_" + "a" * 32, claim="x")

    with pytest.raises(ValidationError):
        CreateReviewRequest(
            document_id="doc_" + "a" * 32,
            claim="A sufficiently clear claim",
            hidden_prompt="not allowed",
        )


def test_review_schema_rejects_unknown_verdict() -> None:
    with pytest.raises(ValidationError):
        ReviewResponse(
            review_id="rev_" + "b" * 32,
            document_id="doc_" + "a" * 32,
            claim="Revenue increased by 27 percent.",
            verdict="MAYBE",
            reasoning="Unknown labels are forbidden.",
            evidence=[],
            model="mock/test",
            created_at=datetime.now(UTC),
        )

    assert Verdict.SUPPORTED.value == "SUPPORTED"
