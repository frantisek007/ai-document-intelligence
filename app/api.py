import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.database import (
    compare_processing_runs,
    get_all_processing_runs,
    get_processing_run,
    get_processing_runs,
    init_db,
)
from app.processor import process_document
from app.exceptions import (
    DocumentTextExtractionError,
    UnsupportedDocumentError,
)

from app.evaluation import (
    evaluate_all_runs,
    evaluate_extraction,
    load_ground_truth,
)


app = FastAPI(
    title="AI Document Intelligence API",
    version="0.1.0",
)

UPLOAD_DIR = Path("uploads")


@app.on_event("startup")
def startup() -> None:
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok"
    }


@app.post("/documents/process")
def process_uploaded_document(
    file: UploadFile = File(...)
) -> dict:

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as target:
            shutil.copyfileobj(file.file, target)

        result = process_document(
            str(file_path),
            original_filename=file.filename,
        )

        return result

    except UnsupportedDocumentError as exc:
        raise HTTPException(
            status_code=415,
            detail=str(exc),
        ) from exc

    except DocumentTextExtractionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Internal document processing error",
        ) from exc

    finally:
        if file_path.exists():
            file_path.unlink()


@app.get("/runs/{run_id}")
def get_run(run_id: int) -> dict:

    run = get_processing_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Processing run not found",
        )

    return run

@app.get("/runs")
def list_runs(limit: int = 20) -> list[dict]:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100",
        )

    return get_processing_runs(limit)

@app.get("/runs/compare/{run_id_a}/{run_id_b}")
def compare_runs(
    run_id_a: int,
    run_id_b: int,
) -> dict:

    comparison = compare_processing_runs(
        run_id_a,
        run_id_b,
    )

    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail="One or both processing runs were not found",
        )

    return comparison

@app.get("/runs/{run_id}/evaluate")
def evaluate_run(run_id: int) -> dict:

    run = get_processing_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Processing run not found",
        )

    ground_truth = load_ground_truth(
        run["filename"]
    )

    if ground_truth is None:
        raise HTTPException(
            status_code=404,
            detail="Ground truth not found for this document",
        )

    evaluation = evaluate_extraction(
        run["extracted_data"],
        ground_truth,
    )

    return {
        "run_id": run_id,
        "filename": run["filename"],
        "prompt_version": run["prompt_version"],
        "evaluation": evaluation,
    }

@app.get("/evaluation")
def evaluate_regression_set(
    prompt_version: str | None = None,
) -> dict:
    runs = get_all_processing_runs()

    return evaluate_all_runs(
        runs,
        prompt_version=prompt_version,
    )