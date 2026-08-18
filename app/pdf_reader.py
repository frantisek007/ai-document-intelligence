from pathlib import Path

from pypdf import PdfReader

from app.exceptions import (
    DocumentTextExtractionError,
    UnsupportedDocumentError,
)


def extract_text_from_pdf(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise UnsupportedDocumentError(
            "Only PDF files are supported."
        )

    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise DocumentTextExtractionError(
            "The PDF could not be read."
        ) from exc

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    result = "\n\n".join(pages)

    if not result.strip():
        from app.ocr_service import extract_text_with_ocr

        result = extract_text_with_ocr(file_path)

        if not result.strip():
            raise DocumentTextExtractionError(
                "No readable text could be extracted, including OCR."
            )

    return result