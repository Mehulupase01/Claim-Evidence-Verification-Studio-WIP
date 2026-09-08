import json
import logging
import re
import time
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.errors import (
    GroundingError,
    VerifierConfigurationError,
    VerifierError,
    VerifierTimeoutError,
)
from app.models import LLMDecision, RankedChunk, Verdict


logger = logging.getLogger("claim_verifier.verifier")
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": [verdict.value for verdict in Verdict],
            "description": "The claim's status using only the supplied passages.",
        },
        "reasoning": {
            "type": "string",
            "description": "A short factual explanation grounded only in the passages.",
        },
        "evidence_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Only IDs copied from the supplied passages.",
        },
    },
    "required": ["verdict", "reasoning", "evidence_ids"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTION = """You verify one claim using only the supplied source passages.
Return exactly one verdict: SUPPORTED, CONTRADICTED, or INSUFFICIENT_EVIDENCE.
SUPPORTED means the supplied evidence directly establishes the material claim.
CONTRADICTED means the supplied evidence directly conflicts with the material claim.
Choose INSUFFICIENT_EVIDENCE when the passages are absent, incomplete, or ambiguous.
Do not use outside knowledge. Select only supplied evidence IDs. Keep reasoning concise and factual."""


class LLMVerifier(Protocol):
    @property
    def model_identifier(self) -> str: ...

    async def verify(
        self, claim: str, evidence: list[RankedChunk]
    ) -> LLMDecision: ...


class GeminiVerifier:
    """Gemini structured-output adapter with application-side semantic validation."""

    def __init__(
        self, settings: Settings, *, client: httpx.AsyncClient | None = None
    ) -> None:
        self._settings = settings
        self._client = client

    @property
    def model_identifier(self) -> str:
        return f"gemini/{self._settings.gemini_model}"

    async def verify(
        self, claim: str, evidence: list[RankedChunk]
    ) -> LLMDecision:
        if (
            not self._settings.gemini_api_key
            or not self._settings.gemini_api_key.get_secret_value()
            or self._settings.gemini_api_key.get_secret_value() == "replace_me"
        ):
            raise VerifierConfigurationError()
        if not MODEL_PATTERN.fullmatch(self._settings.gemini_model):
            raise VerifierConfigurationError("The configured Gemini model name is invalid.")
        if not evidence:
            raise VerifierError("No retrieved evidence was available for verification.")

        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "claim": claim,
                                    "passages": [
                                        {
                                            "evidence_id": item.evidence_id,
                                            "page": item.page,
                                            "text": item.text,
                                        }
                                        for item in evidence
                                    ],
                                },
                                ensure_ascii=False,
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 400,
                "responseMimeType": "application/json",
                "responseJsonSchema": DECISION_SCHEMA,
            },
        }

        response = await self._request(payload)
        decision = self._parse_decision(response)
        self._validate_grounding(decision, evidence)
        return decision

    async def _request(self, payload: dict) -> httpx.Response:
        started = time.perf_counter()
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.request_timeout_seconds)
        )
        try:
            response = await client.post(
                GEMINI_ENDPOINT.format(model=self._settings.gemini_model),
                headers={
                    "x-goog-api-key": self._settings.gemini_api_key.get_secret_value(),
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            logger.info(
                "verification request completed",
                extra={
                    "operation": "generate_content",
                    "dependency": "gemini_api",
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            return response
        except httpx.TimeoutException:
            logger.warning(
                "verification request timed out",
                extra={
                    "operation": "generate_content",
                    "dependency": "gemini_api",
                    "error_type": "timeout",
                },
            )
            raise VerifierTimeoutError() from None
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "verification request failed",
                extra={
                    "operation": "generate_content",
                    "dependency": "gemini_api",
                    "error_type": "http_error",
                    "upstream_status": exc.response.status_code,
                },
            )
            raise VerifierError(
                "The verification service is temporarily unavailable."
            ) from None
        except httpx.HTTPError:
            logger.warning(
                "verification transport failed",
                extra={
                    "operation": "generate_content",
                    "dependency": "gemini_api",
                    "error_type": "transport_error",
                },
            )
            raise VerifierError(
                "The verification service is temporarily unavailable."
            ) from None
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _parse_decision(response: httpx.Response) -> LLMDecision:
        try:
            payload = response.json()
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
            return LLMDecision.model_validate_json(text)
        except (ValueError, KeyError, IndexError, TypeError, ValidationError):
            raise VerifierError() from None

    @staticmethod
    def _validate_grounding(
        decision: LLMDecision, candidates: list[RankedChunk]
    ) -> None:
        candidate_ids = {candidate.evidence_id for candidate in candidates}
        selected_ids = decision.evidence_ids
        if len(selected_ids) != len(set(selected_ids)):
            raise VerifierError("The verification service repeated an evidence reference.")
        if not set(selected_ids).issubset(candidate_ids):
            raise GroundingError()
        if decision.verdict in {Verdict.SUPPORTED, Verdict.CONTRADICTED} and not selected_ids:
            raise VerifierError(
                "A supported or contradicted verdict must reference source evidence."
            )
