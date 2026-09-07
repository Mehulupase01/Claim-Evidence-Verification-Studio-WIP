from fastapi import Depends

from app.config import Settings, get_settings
from app.services.storage import R2Storage, StorageService


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    return R2Storage(settings)
