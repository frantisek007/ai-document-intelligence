from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Address(BaseModel):
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class CompanyData(BaseModel):
    company_name: str
    company_name_evidence: Optional[str] = None

    company_id: Optional[str] = None
    company_id_evidence: Optional[str] = None

    company_register_number: Optional[str] = None
    company_register_number_evidence: Optional[str] = None

    tax_id: Optional[str] = None
    tax_id_evidence: Optional[str] = None

    vat_id: Optional[str] = None
    vat_id_evidence: Optional[str] = None

    legal_form: Optional[str] = None
    legal_form_evidence: Optional[str] = None

    address: Optional[Address] = None

    managing_directors: list[str] = Field(default_factory=list)

    document_date: Optional[date] = None
    document_date_evidence: Optional[str] = None