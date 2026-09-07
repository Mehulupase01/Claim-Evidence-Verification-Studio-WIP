from fastapi import Depends

from app.config import Settings, get_settings
from app.services.extraction import DocumentExtractor, ExtractionService
from app.services.retrieval import BM25Retriever, RetrievalService
from app.services.storage import R2Storage, StorageService


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    return R2Storage(settings)


def get_extraction_service(
    settings: Settings = Depends(get_settings),
) -> ExtractionService:
    return DocumentExtractor(settings)


def get_retrieval_service() -> RetrievalService:
    return BM25Retriever()
