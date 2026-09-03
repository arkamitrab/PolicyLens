# PolicyLens résumé bullets

Use these only after you can explain the architecture and demonstrate the app.

## Three-bullet version

**PolicyLens — Life Insurance Document Intelligence Workbench** | Python,
Streamlit, OCR, scikit-learn, SQLite, OpenAI API (optional)

- Built an evidence-first Streamlit application that converts PDF, image, and
  text-based insurance references into 10+ structured product fields with
  validation flags and a human-review queue.
- Designed an agent-style ingestion, extraction, validation, retrieval, and
  answer workflow with OCR fallback, citation-grounded Q&A, abstention on weak
  evidence, and an optional LLM synthesis layer.
- Implemented an interactive analytics dashboard, product comparison, CSV
  export, SQLite audit logging, synthetic test data, and seven automated tests
  covering extraction, provenance, deduplication, persistence, and reporting.

## One-line version

Built PolicyLens, a Python/Streamlit document-intelligence app using OCR,
structured extraction, grounded retrieval, validation, portfolio analytics, and
SQLite audit trails to turn synthetic life-insurance references into reviewable
product data.

## Interview framing

The problem is not merely extracting text. Insurance teams also need provenance,
quality checks, exception handling, and human review before reference data can
support decisions. PolicyLens therefore keeps page-level citations, surfaces
missing fields, abstains when evidence is weak, and separates deterministic
extraction from optional generative synthesis.
