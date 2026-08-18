import time
from pathlib import Path

from app.database import save_processing_run
from app.llm_service import extract_company_data
from app.pdf_reader import extract_text_from_pdf
from app.validation import (
    calculate_confidence,
    determine_status,
    validate_company_data,
)


MODEL_NAME = "gpt-5.6"
PROMPT_VERSION = "v2"


def process_document(
    pdf_path: str,
    original_filename: str | None = None,
) -> dict:

    start_time = time.perf_counter()

    filename = (
        original_filename
        or Path(pdf_path).name
    )

    text = extract_text_from_pdf(
        pdf_path
    )

    company = extract_company_data(
        text
    )

    validation_result = (
        validate_company_data(
            company
        )
    )

    confidence = calculate_confidence(
        company,
        validation_result,
    )

    status = determine_status(
        validation_result,
        confidence,
    )

    processing_time_ms = int(
        (
            time.perf_counter()
            - start_time
        )
        * 1000
    )

    run_id = save_processing_run(
        filename=filename,
        extracted_data=company.model_dump(
            mode="json"
        ),
        validation_result=validation_result,
        confidence=confidence,
        status=status,
        model_name=MODEL_NAME,
        prompt_version=PROMPT_VERSION,
        processing_time_ms=processing_time_ms,
    )

    return {
        "run_id": run_id,
        "filename": filename,
        "extracted_characters": len(text),
        "company": company.model_dump(
            mode="json"
        ),
        "validation": validation_result,
        "confidence": confidence,
        "status": status,
        "model": MODEL_NAME,
        "prompt_version": PROMPT_VERSION,
        "processing_time_ms": processing_time_ms,
    }