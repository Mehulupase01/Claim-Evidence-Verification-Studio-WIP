import json
import traceback

import httpx
import pytest
from pydantic import SecretStr

from app.config import Settings
from app.errors import (
    GroundingError,
    VerifierConfigurationError,
    VerifierError,
    VerifierTimeoutError,
)
from app.models import RankedChunk, Verdict
from app.services.verifier import GeminiVerifier


def candidate(evidence_id: str = "chunk_0001") -> RankedChunk:
    return RankedChunk(
        evidence_id=evidence_id,
        page=2,
        text="Revenue increased by 27 percent during the second quarter.",
        start_char=20,
        end_char=79,
        retrieval_score=1.25,
    )


def gemini_response(decision: dict) -> httpx.Response:
    request = httpx.Request("POST", "https://example.invalid")
    return httpx.Response(
        200,
        request=request,
        json={
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(decision)}]}}
            ]
        },
    )


def settings() -> Settings:
    return Settings(
        _env_file=None,
        gemini_api_key=SecretStr("unit_test_placeholder"),
        gemini_model="gemini-3.5-flash-lite",
    )


@pytest.mark.parametrize(
    ("verdict", "evidence_ids"),
    [
        (Verdict.SUPPORTED, ["chunk_0001"]),
        (Verdict.CONTRADICTED, ["chunk_0001"]),
        (Verdict.INSUFFICIENT_EVIDENCE, []),
    ],
)
@pytest.mark.asyncio
async def test_three_way_structured_decisions(verdict, evidence_ids) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "unit_test_placeholder"
        body = json.loads(request.content)
        prompt = json.loads(body["contents"][0]["parts"][0]["text"])
        assert prompt["passages"][0]["evidence_id"] == "chunk_0001"
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        return gemini_response(
            {
                "verdict": verdict.value,
                "reasoning": "The supplied passage determines the result.",
                "evidence_ids": evidence_ids,
            }
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GeminiVerifier(settings(), client=client).verify(
            "Revenue increased 27 percent in Q2.", [candidate()]
        )

    assert result.verdict == verdict
    assert result.evidence_ids == evidence_ids


@pytest.mark.asyncio
async def test_unknown_evidence_id_is_rejected() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return gemini_response(
            {
                "verdict": "SUPPORTED",
                "reasoning": "An invented citation must not be accepted.",
                "evidence_ids": ["chunk_9999"],
            }
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GroundingError):
            await GeminiVerifier(settings(), client=client).verify(
                "A claim", [candidate()]
            )


@pytest.mark.asyncio
async def test_malformed_provider_response_is_rejected() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": "not-json"}]}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(VerifierError):
            await GeminiVerifier(settings(), client=client).verify(
                "A claim", [candidate()]
            )


@pytest.mark.asyncio
async def test_timeout_maps_to_bounded_timeout_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(VerifierTimeoutError):
            await GeminiVerifier(settings(), client=client).verify(
                "A claim", [candidate()]
            )


@pytest.mark.asyncio
async def test_http_failure_does_not_put_api_key_in_traceback() -> None:
    sensitive_value = "credential_that_must_never_reach_a_traceback"

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, request=request)

    configured = Settings(
        _env_file=None,
        gemini_api_key=SecretStr(sensitive_value),
        gemini_model="gemini-3.5-flash-lite",
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(VerifierError) as captured:
            await GeminiVerifier(configured, client=client).verify(
                "A claim", [candidate()]
            )

    rendered_traceback = "".join(traceback.format_exception(captured.value))
    assert sensitive_value not in rendered_traceback


@pytest.mark.asyncio
async def test_missing_api_key_fails_before_network_call() -> None:
    with pytest.raises(VerifierConfigurationError):
        await GeminiVerifier(
            Settings(_env_file=None, gemini_api_key=None)
        ).verify("A claim", [candidate()])


@pytest.mark.asyncio
async def test_supported_decision_requires_evidence() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return gemini_response(
            {
                "verdict": "SUPPORTED",
                "reasoning": "This response is semantically incomplete.",
                "evidence_ids": [],
            }
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(VerifierError, match="must reference"):
            await GeminiVerifier(settings(), client=client).verify(
                "A claim", [candidate()]
            )


@pytest.mark.asyncio
async def test_duplicate_evidence_ids_are_rejected() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return gemini_response(
            {
                "verdict": "SUPPORTED",
                "reasoning": "Duplicate references add no grounding.",
                "evidence_ids": ["chunk_0001", "chunk_0001"],
            }
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(VerifierError, match="repeated"):
            await GeminiVerifier(settings(), client=client).verify(
                "A claim", [candidate()]
            )
