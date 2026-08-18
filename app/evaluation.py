import json
from pathlib import Path


GROUND_TRUTH_PATH = Path("evaluation/ground_truth.json")


def load_ground_truth(filename: str) -> dict | None:
    if not GROUND_TRUTH_PATH.exists():
        return None

    with open(
        GROUND_TRUTH_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return data.get(filename)


def normalize_value(value, field_name: str | None = None):
    if value is None:
        return None

    if isinstance(value, str):
        normalized = value.strip().lower()

        if field_name == "legal_form":
            legal_form_aliases = {
                "a. s.": "a.s.",
                "a.s.": "a.s.",
                "akciová spoločnosť (a. s.)": "a.s.",
                "akciová spoločnosť": "a.s.",

                "spol. s r.o.": "s.r.o.",
                "spol. s r. o.": "s.r.o.",
                "s.r.o.": "s.r.o.",
                "s. r. o.": "s.r.o.",
                "spoločnosť s ručením obmedzeným": "s.r.o.",
            }

            return legal_form_aliases.get(
                normalized,
                normalized,
            )

        return normalized

    return value


def compare_field(
    actual,
    expected,
    field_name: str | None = None,
) -> bool:
    return (
        normalize_value(actual, field_name)
        == normalize_value(expected, field_name)
    )


def evaluate_extraction(
    actual: dict,
    expected: dict,
) -> dict:

    results = {}

    fields = [
        "company_name",
        "company_id",
        "company_register_number",
        "tax_id",
        "vat_id",
        "legal_form",
        "document_date",
    ]

    correct = 0
    total = 0

    for field in fields:
        actual_value = actual.get(field)
        expected_value = expected.get(field)

        match = compare_field(
            actual_value,
            expected_value,
            field,
        )

        results[field] = {
            "actual": actual_value,
            "expected": expected_value,
            "match": match,
        }

        total += 1

        if match:
            correct += 1

    actual_address = actual.get("address") or {}
    expected_address = expected.get("address") or {}

    address_fields = [
        "street",
        "postal_code",
        "city",
        "country",
    ]

    for field in address_fields:
        key = f"address.{field}"

        actual_value = actual_address.get(field)
        expected_value = expected_address.get(field)

        match = compare_field(
            actual_value,
            expected_value,
        )

        results[key] = {
            "actual": actual_value,
            "expected": expected_value,
            "match": match,
        }

        total += 1

        if match:
            correct += 1

    accuracy = round(
        correct / total,
        3,
    ) if total else 0.0

    return {
        "correct_fields": correct,
        "total_fields": total,
        "accuracy": accuracy,
        "fields": results,
    }

def evaluate_all_runs(
    runs: list[dict],
    prompt_version: str | None = None,
) -> dict:
    latest_runs_by_filename = {}

    for run in runs:
        if (
            prompt_version is not None
            and run["prompt_version"] != prompt_version
        ):
            continue

        filename = run["filename"]

        current = latest_runs_by_filename.get(filename)

        if current is None or run["id"] > current["id"]:
            latest_runs_by_filename[filename] = run

    documents = []
    total_correct = 0
    total_fields = 0

    for run in latest_runs_by_filename.values():
        ground_truth = load_ground_truth(
            run["filename"]
        )

        if ground_truth is None:
            continue

        evaluation = evaluate_extraction(
            run["extracted_data"],
            ground_truth,
        )

        documents.append(
            {
                "run_id": run["id"],
                "filename": run["filename"],
                "prompt_version": run["prompt_version"],
                "accuracy": evaluation["accuracy"],
                "correct_fields": evaluation["correct_fields"],
                "total_fields": evaluation["total_fields"],
            }
        )

        total_correct += evaluation["correct_fields"]
        total_fields += evaluation["total_fields"]

    overall_accuracy = (
        round(total_correct / total_fields, 3)
        if total_fields
        else 0.0
    )

    return {
        "prompt_version": prompt_version,
        "documents": len(documents),
        "correct_fields": total_correct,
        "total_fields": total_fields,
        "overall_accuracy": overall_accuracy,
        "results": documents,
    }