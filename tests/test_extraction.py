from io import BytesIO

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.config import Settings
from app.errors import ExtractionError
from app.services.extraction import DocumentExtractor


def make_text_pdf(pages: list[str]) -> bytes:
    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_reference}
                )
            }
        )
        content = DecodedStreamObject()
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content.set_data(f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.asyncio
async def test_text_extraction_assigns_stable_chunks_and_offsets() -> None:
    extractor = DocumentExtractor(
        Settings(_env_file=None, chunk_size_chars=300, chunk_overlap_chars=40)
    )
    paragraph = "Revenue increased by 27 percent during the second quarter. "
    payload = (paragraph * 12).encode()

    first = await extractor.extract(
        document_id="doc_" + "a" * 32,
        filename="report.txt",
        content_type="text/plain",
        data=payload,
    )
    second = await extractor.extract(
        document_id="doc_" + "a" * 32,
        filename="report.txt",
        content_type="text/plain",
        data=payload,
    )

    assert len(first.chunks) > 1
    assert [chunk.evidence_id for chunk in first.chunks] == [
        chunk.evidence_id for chunk in second.chunks
    ]
    assert first.chunks[0].start_char == 0
    assert all(chunk.page == 1 for chunk in first.chunks)


@pytest.mark.asyncio
async def test_pdf_extraction_preserves_page_numbers() -> None:
    extractor = DocumentExtractor(Settings(_env_file=None))
    payload = make_text_pdf(
        [
            "The first page discusses customer growth.",
            "The second page states revenue increased by 27 percent.",
        ]
    )

    extracted = await extractor.extract(
        document_id="doc_" + "b" * 32,
        filename="report.pdf",
        content_type="application/pdf",
        data=payload,
    )

    assert extracted.page_count == 2
    assert [chunk.page for chunk in extracted.chunks] == [1, 2]
    assert "27 percent" in extracted.chunks[1].text


@pytest.mark.asyncio
async def test_blank_pdf_fails_with_ocr_limitation() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)

    with pytest.raises(ExtractionError, match="OCR"):
        await DocumentExtractor(Settings(_env_file=None)).extract(
            document_id="doc_" + "c" * 32,
            filename="scan.pdf",
            content_type="application/pdf",
            data=output.getvalue(),
        )


@pytest.mark.asyncio
async def test_non_utf8_text_is_rejected() -> None:
    with pytest.raises(ExtractionError, match="UTF-8"):
        await DocumentExtractor(Settings(_env_file=None)).extract(
            document_id="doc_" + "d" * 32,
            filename="report.txt",
            content_type="text/plain",
            data=b"\xff\xfe\xfa",
        )
