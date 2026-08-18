import re
from datetime import date

from app.models import CompanyData


def is_valid_slovak_ico(ico: str) -> bool:
    ico = re.sub(r"\s+", "", ico)

    if not ico.isdigit() or len(ico) != 8:
        return False

    weights = [8, 7, 6, 5, 4, 3, 2]

    weighted_sum = sum(
        int(ico[i]) * weights[i]
        for i in range(7)
    )

    remainder = weighted_sum % 11
    check_digit = (11 - remainder) % 10

    return check_digit == int(ico[7])


def is_slovak_company(company: CompanyData) -> bool:
    if company.address and company.address.country:
        country = company.address.country.lower().strip()

        return country in {
            "slovakia",
            "slovensko",
            "slovak republic",
            "slovenská republika",
        }

    if company.vat_id:
        normalized_vat = (
            company.vat_id
            .replace(" ", "")
            .upper()
        )

        return normalized_vat.startswith("SK")

    return False


def validate_company_data(
    company: CompanyData,
) -> dict:

    errors = []
    warnings = []

    # Company name
    if not company.company_name.strip():
        errors.append(
            "company_name is missing"
        )

    # Company ID
    if company.company_id:

        normalized_ico = re.sub(
            r"\s+",
            "",
            company.company_id,
        )

        if is_slovak_company(company):

            if not normalized_ico.isdigit():
                errors.append(
                    "company_id must contain only digits"
                )

            elif len(normalized_ico) != 8:
                errors.append(
                    "company_id must have 8 digits"
                )

            elif not is_valid_slovak_ico(
                normalized_ico
            ):
                errors.append(
                    "company_id failed Slovak IČO checksum validation"
                )

    else:
        warnings.append(
            "company_id is missing"
        )

    # Slovakia-specific VAT and tax validation
    if is_slovak_company(company):

        if company.vat_id:

            normalized_vat = (
                company.vat_id
                .replace(" ", "")
                .upper()
            )

            if not re.fullmatch(
                r"SK\d{10}",
                normalized_vat,
            ):
                warnings.append(
                    "vat_id does not match Slovak VAT format"
                )

        if company.tax_id:

            normalized_tax_id = (
                company.tax_id
                .replace(" ", "")
            )

            if not re.fullmatch(
                r"\d{10}",
                normalized_tax_id,
            ):
                warnings.append(
                    "tax_id does not match Slovak tax ID format"
                )

    # Address
    if company.address:

        if not company.address.country:
            warnings.append(
                "country is missing"
            )

        if not company.address.city:
            errors.append(
                "city is missing"
            )

    else:
        warnings.append(
            "address is missing"
        )

    # Document date
    if company.document_date is None:

        warnings.append(
            "document_date is missing"
        )

    else:
        current_year = date.today().year

        if company.document_date.year < 1900:
            errors.append(
                "document_date contains an implausible year"
            )

        elif company.document_date.year > current_year + 1:
            errors.append(
                "document_date is implausibly far in the future"
            )

    return {
        "errors": errors,
        "warnings": warnings,
    }


def calculate_confidence(
    company: CompanyData,
    validation_result: dict,
) -> float:

    score = 1.0

    score -= (
        0.25
        * len(validation_result["errors"])
    )

    score -= (
        0.08
        * len(validation_result["warnings"])
    )

    evidence_fields = [
        company.company_name_evidence,
        company.company_id_evidence,
        company.company_register_number_evidence,
        company.tax_id_evidence,
        company.vat_id_evidence,
        company.legal_form_evidence,
        company.document_date_evidence,
    ]

    missing_evidence = sum(
        1
        for evidence in evidence_fields
        if evidence is None
    )

    score -= 0.03 * missing_evidence

    return max(
        0.0,
        min(
            1.0,
            round(score, 2),
        ),
    )


def determine_status(
    validation_result: dict,
    confidence: float,
) -> str:

    if validation_result["errors"]:
        return "REJECTED"

    if confidence >= 0.90:
        return "AUTO_APPROVED"

    if confidence >= 0.70:
        return "REVIEW"

    return "REJECTED"