import asyncio
from collections.abc import Mapping
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings
from app.errors import ObjectNotFoundError, StorageConfigurationError, StorageError


class StorageService(Protocol):
    async def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> None: ...

    async def get_bytes(self, key: str) -> bytes: ...

    async def exists(self, key: str) -> bool: ...

    async def delete(self, key: str) -> None: ...


def _usable_secret(value: str | None) -> bool:
    return bool(value and value != "replace_me" and "<" not in value)


class R2Storage:
    """Cloudflare R2 adapter using the S3-compatible object API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client_instance = None

    def _client(self):
        if self._client_instance is not None:
            return self._client_instance

        access_key = (
            self._settings.r2_access_key_id.get_secret_value()
            if self._settings.r2_access_key_id
            else None
        )
        secret_key = (
            self._settings.r2_secret_access_key.get_secret_value()
            if self._settings.r2_secret_access_key
            else None
        )
        if not (
            _usable_secret(self._settings.r2_endpoint)
            and _usable_secret(access_key)
            and _usable_secret(secret_key)
            and _usable_secret(self._settings.r2_bucket)
        ):
            raise StorageConfigurationError()

        timeout = self._settings.request_timeout_seconds
        self._client_instance = boto3.client(
            "s3",
            endpoint_url=self._settings.r2_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                connect_timeout=min(timeout, 5.0),
                read_timeout=timeout,
                retries={"total_max_attempts": 2, "mode": "standard"},
            ),
        )
        return self._client_instance

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        def put() -> None:
            self._client().put_object(
                Bucket=self._settings.r2_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata=dict(metadata or {}),
            )

        await self._call(put)

    async def get_bytes(self, key: str) -> bytes:
        def get() -> bytes:
            response = self._client().get_object(
                Bucket=self._settings.r2_bucket,
                Key=key,
            )
            body = response["Body"]
            try:
                return body.read()
            finally:
                body.close()

        return await self._call(get, missing_is_not_found=True)

    async def exists(self, key: str) -> bool:
        def head() -> bool:
            self._client().head_object(Bucket=self._settings.r2_bucket, Key=key)
            return True

        try:
            return await self._call(head, missing_is_not_found=True)
        except ObjectNotFoundError:
            return False

    async def delete(self, key: str) -> None:
        def remove() -> None:
            self._client().delete_object(Bucket=self._settings.r2_bucket, Key=key)

        await self._call(remove)

    async def _call(self, operation, *, missing_is_not_found: bool = False):
        try:
            return await asyncio.to_thread(operation)
        except StorageConfigurationError:
            raise
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if missing_is_not_found and error_code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                raise ObjectNotFoundError() from None
            raise StorageError() from None
        except (BotoCoreError, OSError):
            raise StorageError() from None


class InMemoryStorage:
    """Deterministic test double; never presented as a real integration."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.objects[key] = bytes(data)
        self.content_types[key] = content_type

    async def get_bytes(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError:
            raise ObjectNotFoundError() from None

    async def exists(self, key: str) -> bool:
        return key in self.objects

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)
        self.content_types.pop(key, None)
