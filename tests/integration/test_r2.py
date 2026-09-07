import os
import uuid

import pytest

from app.config import Settings
from app.services.storage import R2Storage


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("R2_INTEGRATION") != "1",
    reason="Set R2_INTEGRATION=1 with user-owned R2 credentials to run.",
)
@pytest.mark.asyncio
async def test_real_r2_round_trip() -> None:
    storage = R2Storage(Settings(_env_file=None))
    key = f"integration-tests/{uuid.uuid4().hex}.txt"
    payload = b"claim-verifier-r2-round-trip"

    try:
        await storage.put_bytes(key, payload, content_type="text/plain")
        assert await storage.exists(key)
        assert await storage.get_bytes(key) == payload
    finally:
        await storage.delete(key)
