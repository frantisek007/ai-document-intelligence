from dotenv import load_dotenv
from openai import OpenAI

from app.models import CompanyData


load_dotenv()

client = OpenAI()


def extract_company_data(text: str) -> CompanyData:
    completion = client.chat.completions.parse(
        model="gpt-5.6",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract structured information about the main legal entity "
                    "that issued or provides the document. "
                    "Only use information explicitly present in the document. "
                    "Do not infer or invent missing information. "

                    "For every extracted field, also return a short evidence snippet "
                    "copied from the document that supports the extracted value. "

                    "Distinguish carefully between company identifiers. "
                    "company_id means a national company identifier such as Slovak IČO. "
                    "company_register_number means a commercial register number. "
                    "tax_id means a national tax identifier. "
                    "vat_id means a VAT identifier. "

                    "An identifier prefixed with an EU country code such as SK, CZ, AT or DE "
                    "should normally be treated as a VAT identifier when the document context "
                    "supports this interpretation. "
                    "Do not convert a VAT identifier into a national tax identifier. "

                    "Return document_date in ISO format YYYY-MM-DD. "
                    "Convert dates such as 04.06.2026 to 2026-06-04. "
                    "Never invent a date that is not supported by the evidence. "

                    "If a value is unavailable, return null and its evidence should also be null."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        response_format=CompanyData,
    )

    result = completion.choices[0].message.parsed

    if result is None:
        raise ValueError(
            "The model did not return structured company data."
        )

    return result
    