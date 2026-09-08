import os

import pytest

from app.config import Settings
from app.models import RankedChunk, Verdict
from app.services.verifier import GeminiVerifier


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("GEMINI_INTEGRATION") != "1",
    reason="Set GEMINI_INTEGRATION=1 with a user-owned Gemini API key to run.",
)
@pytest.mark.asyncio
async def test_real_gemini_structured_verdict() -> None:
    evidence = RankedChunk(
        evidence_id="chunk_0001",
        page=1,
        text="The launch date is 18 September 2026.",
        start_char=0,
        end_char=38,
        retrieval_score=1.0,
    )

    result = await GeminiVerifier(Settings()).verify(
        "The launch date is 18 September 2026.", [evidence]
    )

    assert result.verdict == Verdict.SUPPORTED
    assert result.evidence_ids == ["chunk_0001"]
