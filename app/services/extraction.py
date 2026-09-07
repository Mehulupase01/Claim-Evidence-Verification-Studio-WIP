import asyncio
from dataclasses import dataclass
from io import BytesIO
import re
from typing import Protocol

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import Settings
from app.errors import ExtractionError
from app.models import EvidenceChunk, ExtractedDocument


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


class ExtractionService(Protocol):
    async def extract(
        self,
        *,
        document_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ExtractedDocument: ...


class DocumentExtractor:
    """Bounded extraction for UTF-8 text and ordinary text-based PDFs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def extract(
        self,
        *,
        document_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ExtractedDocument:
        return await asyncio.to_thread(
            self._extract_sync,
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            data=data,
        )

    def _extract_sync(
        self,
        *,
        document_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ExtractedDocument:
        if content_type == "text/plain":
            pages = [PageText(page=1, text=self._decode_text(data))]
        elif content_type == "application/pdf":
            pages = self._extract_pdf(data)
        else:
            raise ExtractionError("This file type cannot be extracted.")

        normalized_pages: list[PageText] = []
        total_characters = 0
        for page in pages:
            text = normalize_text(page.text)
            total_characters += len(text)
            if total_characters > self._settings.max_extracted_chars:
                raise ExtractionError(
                    "The document contains more extractable text than this reviewer accepts."
                )
            if text:
                normalized_pages.append(PageText(page=page.page, text=text))

        if not normalized_pages or not any(
            re.search(r"[\w\d]", page.text, flags=re.UNICODE)
            for page in normalized_pages
        ):
            raise ExtractionError(
                "No usable text was found. Scanned PDFs need OCR, which this version does not perform."
            )

        chunks = chunk_pages(
            normalized_pages,
            chunk_size=self._settings.chunk_size_chars,
            overlap=self._settings.chunk_overlap_chars,
        )
        if not chunks:
            raise ExtractionError()

        return ExtractedDocument(
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            page_count=len(pages),
            chunks=chunks,
        )

    def _decode_text(self, data: bytes) -> str:
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ExtractionError("Plain-text files must use UTF-8 encoding.") from None

    def _extract_pdf(self, data: bytes) -> list[PageText]:
        try:
            reader = PdfReader(BytesIO(data), strict=False)
            if reader.is_encrypted and reader.decrypt("") == 0:
                raise ExtractionError("Password-protected PDFs are not supported.")
            if len(reader.pages) > self._settings.max_document_pages:
                raise ExtractionError(
                    f"PDFs are limited to {self._settings.max_document_pages} pages."
                )
            return [
                PageText(page=number, text=page.extract_text() or "")
                for number, page in enumerate(reader.pages, start=1)
            ]
        except ExtractionError:
            raise
        except (PdfReadError, ValueError, TypeError, OSError):
            raise ExtractionError(
                "The PDF could not be read. Upload an ordinary text-based PDF."
            ) from None


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_pages(
    pages: list[PageText], *, chunk_size: int, overlap: int
) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for page in pages:
        cursor = 0
        while cursor < len(page.text):
            proposed_end = min(cursor + chunk_size, len(page.text))
            end = _natural_boundary(page.text, cursor, proposed_end, chunk_size)

            raw = page.text[cursor:end]
            leading = len(raw) - len(raw.lstrip())
            trailing = len(raw.rstrip())
            start_char = cursor + leading
            end_char = cursor + trailing
            snippet = raw.strip()
            if snippet:
                chunks.append(
                    EvidenceChunk(
                        evidence_id=f"chunk_{len(chunks) + 1:04d}",
                        page=page.page,
                        text=snippet,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )

            if end >= len(page.text):
                break
            cursor = max(cursor + 1, end - overlap)
            while cursor < end and page.text[cursor].isspace():
                cursor += 1
    return chunks


def _natural_boundary(text: str, start: int, proposed_end: int, size: int) -> int:
    if proposed_end >= len(text):
        return len(text)
    minimum = start + max(1, size // 2)
    candidates = (
        text.rfind("\n\n", minimum, proposed_end),
        text.rfind(". ", minimum, proposed_end),
        text.rfind(" ", minimum, proposed_end),
    )
    boundary = max(candidates)
    if boundary < minimum:
        return proposed_end
    if text[boundary : boundary + 2] in {"\n\n", ". "}:
        return boundary + 1
    return boundary
