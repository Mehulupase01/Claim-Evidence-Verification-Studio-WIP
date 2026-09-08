from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.dependencies import get_storage_service
from app.errors import StorageError
from app.main import app
from app.services.storage import InMemoryStorage


async def post_file(
    storage,
    filename: str,
    data: bytes,
    content_type: str,
    settings: Settings | None = None,
):
    app.dependency_overrides[get_storage_service] = lambda: storage
    if settings:
        app.dependency_overrides[get_settings] = lambda: settings
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post(
                "/documents", files={"file": (filename, BytesIO(data), content_type)}
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unsupported_extension_returns_415_before_storage() -> None:
    storage = InMemoryStorage()

    response = await post_file(
        storage, "installer.exe", b"not executable", "application/octet-stream"
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file"
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_mismatched_mime_type_returns_415() -> None:
    response = await post_file(
        InMemoryStorage(), "report.pdf", b"%PDF", "image/png"
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_oversized_upload_returns_413() -> None:
    settings = Settings(_env_file=None, max_upload_mb=1)
    response = await post_file(
        InMemoryStorage(),
        "report.txt",
        b"x" * (settings.max_upload_bytes + 1),
        "text/plain",
        settings,
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"


@pytest.mark.asyncio
async def test_valid_text_upload_is_stored_under_namespaced_key() -> None:
    storage = InMemoryStorage()
    payload = b"Quarterly revenue increased by 27 percent."

    response = await post_file(storage, "report.txt", payload, "text/plain")

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"].startswith("doc_")
    expected_key = f"documents/{body['document_id']}/original.txt"
    assert storage.objects[expected_key] == payload
    assert body["page_count"] == 1
    assert body["chunk_count"] == 1
    sidecar_key = f"documents/{body['document_id']}/extracted.json"
    assert sidecar_key in storage.objects


@pytest.mark.asyncio
async def test_empty_text_document_returns_explicit_processing_error() -> None:
    storage = InMemoryStorage()

    response = await post_file(storage, "empty.txt", b" \n\t ", "text/plain")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "extraction_failed"
    assert storage.objects == {}


class FailingStorage(InMemoryStorage):
    async def put_bytes(self, *args, **kwargs) -> None:
        raise StorageError()


@pytest.mark.asyncio
async def test_storage_failure_is_safe_and_contains_request_id() -> None:
    response = await post_file(
        FailingStorage(),
        "report.txt",
        b"This content is long enough to pass text extraction safely.",
        "text/plain",
    )

    assert response.status_code == 502
    body = response.json()["error"]
    assert body["code"] == "storage_unavailable"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "credential" not in response.text.lower()


class SidecarFailingStorage(InMemoryStorage):
    async def put_bytes(self, key, data, *, content_type, metadata=None) -> None:
        if key.endswith("/extracted.json"):
            raise StorageError()
        await super().put_bytes(
            key, data, content_type=content_type, metadata=metadata
        )


@pytest.mark.asyncio
async def test_sidecar_failure_rolls_back_the_original_object() -> None:
    storage = SidecarFailingStorage()

    response = await post_file(
        storage,
        "report.txt",
        b"This content is long enough to be extracted before the write fails.",
        "text/plain",
    )

    assert response.status_code == 502
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_upload_filename_is_reduced_to_its_safe_basename() -> None:
    storage = InMemoryStorage()

    response = await post_file(
        storage,
        "../../private/report.txt",
        b"A valid report body that contains enough text for extraction.",
        "text/plain",
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "report.txt"
