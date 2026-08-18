import json
import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )


def init_db() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS processing_runs (
                    id BIGSERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    extracted_data JSONB NOT NULL,
                    validation_result JSONB NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    status TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    processing_time_ms INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

        connection.commit()


def save_processing_run(
    filename: str,
    extracted_data: dict,
    validation_result: dict,
    confidence: float,
    status: str,
    model_name: str,
    prompt_version: str,
    processing_time_ms: int,
) -> int:

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO processing_runs (
                    filename,
                    extracted_data,
                    validation_result,
                    confidence,
                    status,
                    model_name,
                    prompt_version,
                    processing_time_ms
                )
                VALUES (
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    filename,
                    json.dumps(
                        extracted_data,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        validation_result,
                        ensure_ascii=False,
                    ),
                    confidence,
                    status,
                    model_name,
                    prompt_version,
                    processing_time_ms,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    return row["id"]


def get_processing_run(
    run_id: int,
) -> dict | None:

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM processing_runs
                WHERE id = %s
                """,
                (run_id,),
            )

            row = cursor.fetchone()

    return row


def get_processing_runs(
    limit: int = 20,
) -> list[dict]:

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    filename,
                    confidence,
                    status,
                    model_name,
                    prompt_version,
                    processing_time_ms,
                    created_at
                FROM processing_runs
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    return rows


def get_all_processing_runs() -> list[dict]:

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM processing_runs
                ORDER BY id ASC
                """
            )

            rows = cursor.fetchall()

    return rows


def compare_processing_runs(
    run_id_a: int,
    run_id_b: int,
) -> dict | None:

    run_a = get_processing_run(run_id_a)
    run_b = get_processing_run(run_id_b)

    if run_a is None or run_b is None:
        return None

    return {
        "run_a": {
            "id": run_a["id"],
            "prompt_version": run_a["prompt_version"],
            "confidence": run_a["confidence"],
            "status": run_a["status"],
            "extracted_data": run_a["extracted_data"],
            "validation_result": run_a["validation_result"],
        },
        "run_b": {
            "id": run_b["id"],
            "prompt_version": run_b["prompt_version"],
            "confidence": run_b["confidence"],
            "status": run_b["status"],
            "extracted_data": run_b["extracted_data"],
            "validation_result": run_b["validation_result"],
        },
        "confidence_change": round(
            run_b["confidence"]
            - run_a["confidence"],
            2,
        ),
    }