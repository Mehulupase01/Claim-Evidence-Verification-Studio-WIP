from pathlib import PurePosixPath
import json
import logging
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.config import Settings, get_settings
from app.dependencies import get_extraction_service, get_storage_service
from app.errors import (
    InvalidUploadError,
    StorageError,
    UnsupportedFileError,
    UploadTooLargeError,
)
from app.models import DocumentUploadResponse
from app.services.extraction import ExtractionService
from app.services.storage import StorageService


router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger("claim_verifier.documents")

ALLOWED_TYPES = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
}


def normalize_filename(filename: str | None) -> tuple[str, str]:
    clean_name = PurePosixPath((filename or "").replace("\\", "/")).name.strip()
    if not clean_name or any(ord(character) < 32 for character in clean_name):
        raise InvalidUploadError("Give the uploaded document a valid filename.")
    if len(clean_name) > 255:
        raise InvalidUploadError("The filename must be 255 characters or fewer.")
    extension = PurePosixPath(clean_name).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise UnsupportedFileError()
    return clean_name, extension


def validate_content_type(extension: str, content_type: str | None) -> str:
    normalized = (content_type or "application/octet-stream").split(";", 1)[0].lower()
    if normalized not in ALLOWED_TYPES[extension]:
        raise UnsupportedFileError()
    return "text/plain" if extension == ".txt" else "application/pdf"


async def read_bounded_upload(file: UploadFile, maximum_bytes: int) -> bytes:
    try:
        data = await file.read(maximum_bytes + 1)
    finally:
        await file.close()
    if not data:
        raise InvalidUploadError()
    if len(data) > maximum_bytes:
        raise UploadTooLargeError(
            f"The file is larger than the configured {maximum_bytes // (1024 * 1024)} MB limit."
        )
    return data


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage_service),
    extractor: ExtractionService = Depends(get_extraction_service),
) -> DocumentUploadResponse:
    filename, extension = normalize_filename(file.filename)
    content_type = validate_content_type(extension, file.content_type)
    data = await read_bounded_upload(file, settings.max_upload_bytes)

    document_id = f"doc_{uuid.uuid4().hex}"
    object_key = f"documents/{document_id}/original{extension}"
    extracted = await extractor.extract(
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        data=data,
    )
    await storage.put_bytes(
        object_key,
        data,
        content_type=content_type,
        metadata={"document-id": document_id},
    )
    try:
        await storage.put_bytes(
            f"documents/{document_id}/extracted.json",
            json.dumps(
                extracted.model_dump(mode="json"), separators=(",", ":")
            ).encode("utf-8"),
            content_type="application/json",
            metadata={"document-id": document_id},
        )
    except StorageError:
        try:
            await storage.delete(object_key)
        except StorageError:
            logger.warning(
                "could not remove original after sidecar failure",
                extra={
                    "operation": "rollback_document_upload",
                    "document_id": document_id,
                    "error_type": "rollback_failed",
                },
            )
        raise
    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        page_count=extracted.page_count,
        chunk_count=len(extracted.chunks),
        created_at=extracted.created_at,
    )
