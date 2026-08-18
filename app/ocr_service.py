import io
import os

import pymupdf
import pytesseract
from PIL import Image


tesseract_cmd = os.getenv("TESSERACT_CMD")

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text_with_ocr(pdf_path: str) -> str:
    document = pymupdf.open(pdf_path)

    pages = []

    try:
        for page in document:
            pixmap = page.get_pixmap(dpi=200)

            image = Image.open(
                io.BytesIO(pixmap.tobytes("png"))
            )

            text = pytesseract.image_to_string(
                image,
                lang="eng",
            )

            if text.strip():
                pages.append(text)

    finally:
        document.close()

    return "\n\n".join(pages)