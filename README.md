# AI Document Intelligence

Enterprise-oriented document processing prototype for extracting, validating, auditing, and evaluating structured company information from PDF documents.

The project demonstrates how an LLM can be integrated as one component of a controlled document-processing pipeline rather than used as a standalone chatbot.

## Architecture

```text
PDF Upload
    |
    v
Native PDF Text Extraction
    |
    +---- no usable text ----> OCR Fallback (Tesseract)
    |                              |
    +------------------------------+
    |
    v
LLM Structured Extraction
    |
    v
Pydantic Schema Validation
    |
    v
Business Validation
    |
    v
Deterministic Confidence Scoring
    |
    v
AUTO_APPROVED / REVIEW / REJECTED
    |
    v
PostgreSQL / JSONB Audit Trail
```

## Features

- PDF text extraction
- OCR fallback for scanned and image-only PDFs
- LLM-based structured information extraction
- Pydantic schemas for structured outputs
- Evidence snippets for extracted values
- Deterministic business validation
- Slovak company ID checksum validation
- Country-aware validation rules
- Confidence scoring based on observable signals
- Human-review routing
- PostgreSQL persistence with JSONB
- Prompt versioning and audit history
- Processing-run comparison
- Ground-truth evaluation
- Field-level accuracy measurement
- Regression evaluation by prompt version
- FastAPI REST API with OpenAPI/Swagger documentation
- Docker and Docker Compose support

## Tech Stack

- Python
- FastAPI
- OpenAI API
- Pydantic
- PyMuPDF
- Tesseract OCR
- PostgreSQL
- JSONB
- Psycopg
- Docker
- Docker Compose

## API

Main endpoints:

```text
GET  /health
POST /documents/process
GET  /runs
GET  /runs/{run_id}
GET  /runs/compare/{run_id_a}/{run_id_b}
GET  /runs/{run_id}/evaluate
GET  /evaluation?prompt_version=v2
```

## Example Processing Flow

A digital PDF is processed through native text extraction.

If no usable text layer is available, the pipeline automatically falls back to OCR using Tesseract.

The extracted text is then passed to the LLM, which returns structured company data according to a predefined Pydantic schema.

Example output fields:

```json
{
  "company_name": "Example GmbH",
  "company_id": "12345678",
  "company_register_number": "FN 123456a",
  "tax_id": "1234567890",
  "vat_id": "ATU12345678",
  "legal_form": "GmbH",
  "address": {
    "street": "Example Street 1",
    "postal_code": "1010",
    "city": "Vienna",
    "country": "Austria"
  }
}
```

Each extracted field can also include an evidence snippet copied from the source document.

## Validation

The project intentionally separates several kinds of validation.

### Schema Validation

Pydantic verifies that the LLM output conforms to the expected technical structure and data types.

### Business Validation

Additional deterministic rules check whether extracted values are plausible.

Examples include:

- required company fields
- Slovak IČO format and checksum
- country-specific tax and VAT rules
- plausible document dates
- required address information

This distinction is important because syntactically valid data is not necessarily factually or semantically valid.

## Confidence and Review

The model does not assign its own confidence score.

Instead, confidence is derived from observable signals such as:

- validation errors
- validation warnings
- missing evidence
- deterministic checks

The resulting score is used to route documents to:

```text
AUTO_APPROVED
REVIEW
REJECTED
```

## Auditability

Every processing run stores metadata including:

- original filename
- extracted structured data
- validation result
- confidence score
- final status
- model name
- prompt version
- processing time
- timestamp

Previous runs are not overwritten.

This allows changes in prompts or models to be compared later.

## PostgreSQL and JSONB

Stable processing metadata is stored relationally, while extracted document data is stored as JSONB.

This keeps the extraction schema flexible while still allowing direct database queries.

Example:

```sql
SELECT
    id,
    extracted_data->>'company_name' AS company_name
FROM processing_runs
WHERE extracted_data->>'vat_id' = 'SK2022187453';
```

## Evaluation

The project includes a small ground-truth regression set.

Prompt versions can be evaluated field by field against known reference data.

### Current Prototype Result

| Metric | Result |
|---|---:|
| Prompt version | `v2` |
| Documents evaluated | 2 |
| Fields evaluated | 22 |
| Correct fields | 22 |
| Field-level accuracy | 100% |

> The 100% result applies only to the current small two-document regression set and must not be interpreted as production-level accuracy.

The purpose of the evaluation layer is to make prompt and model changes measurable and to detect regressions as the dataset grows.

## Running with Docker

Create a `.env` file based on `.env.example` and provide your OpenAI API key.

Then run:

```bash
docker compose build
docker compose up
```

Open the Swagger/OpenAPI documentation at:

`http://localhost:8000/docs`

The Docker Compose setup starts both:

- FastAPI application
- PostgreSQL database

Tesseract OCR is installed directly inside the API container.

## Configuration

Sensitive configuration is supplied through environment variables.

Example:

```text
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_document_intelligence
TESSERACT_CMD=
```

Secrets and real source documents are intentionally excluded from Git.

## Design Principles

The prototype is built around several principles:

- structured outputs instead of free-form LLM responses
- deterministic validation whenever possible
- evidence and traceability
- separation of responsibilities
- prompt and model versioning
- measurable evaluation
- human review for uncertain cases
- reproducible runtime environment

## Key Design Decisions

### Native PDF text first, OCR only as fallback

Digitally generated PDFs are processed using their existing text layer. OCR is only used when no usable text can be extracted.

This avoids unnecessary OCR processing and reduces an additional source of extraction errors.

### LLM for semantic extraction, deterministic code for rules

The LLM is used where semantic understanding is useful. Deterministic validation is preferred whenever a reliable rule exists.

For example, company identifiers and document dates are checked outside the model where possible.

### Prompt versioning

Every processing run stores the prompt version and model name.

This makes it possible to compare the effect of prompt changes on the same source documents.

### Ground-truth regression testing

Prompt changes are evaluated against known reference values instead of being judged only by visual inspection.

This makes quality changes measurable and helps detect regressions.

## Project Structure

```text
ai-document-intelligence/
|
+-- app/
|   +-- api.py
|   +-- database.py
|   +-- evaluation.py
|   +-- exceptions.py
|   +-- llm_service.py
|   +-- models.py
|   +-- ocr_service.py
|   +-- pdf_reader.py
|   +-- processor.py
|   +-- validation.py
|
+-- evaluation/
|   +-- ground_truth.json
|
+-- .dockerignore
+-- .env.example
+-- .gitignore
+-- Dockerfile
+-- docker-compose.yml
+-- requirements.txt
+-- README.md
```

## Future Improvements

Possible next steps include:

- larger and more diverse regression dataset
- German, Slovak, Czech, and English OCR language packs
- asynchronous processing for large documents
- background workers and job queues
- authentication and authorization
- file size and page limits
- malware and file validation
- PostgreSQL migrations
- automated tests and CI
- embeddings and RAG for document search
- production observability and metrics

## Purpose

This project was built as an enterprise-oriented AI engineering prototype focused on practical document intelligence, system integration, validation, auditability, and measurable quality rather than on a standalone chatbot experience.
