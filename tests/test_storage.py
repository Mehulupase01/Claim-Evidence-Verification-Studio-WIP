import pytest

from app.config import Settings
from app.errors import ObjectNotFoundError, StorageConfigurationError
from app.services.storage import InMemoryStorage, R2Storage


@pytest.mark.asyncio
async def test_memory_storage_reports_missing_objects() -> None:
    with pytest.raises(ObjectNotFoundError):
        await InMemoryStorage().get_bytes("missing")


@pytest.mark.asyncio
async def test_r2_adapter_fails_safely_when_credentials_are_missing() -> None:
    settings = Settings(
        _env_file=None,
        r2_endpoint=None,
        r2_access_key_id=None,
        r2_secret_access_key=None,
    )

    with pytest.raises(StorageConfigurationError):
        await R2Storage(settings).exists("any-key")
