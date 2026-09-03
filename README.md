<p align="center">
  <img src="docs/policylens-banner.svg" alt="PolicyLens — evidence-first document intelligence" width="100%">
</p>

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&amp;logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.63%2B-FF4B4B?logo=streamlit&amp;logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/tests-7%20passing-0B6B68">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2878A8">
</p>

# PolicyLens

PolicyLens is a portfolio-grade Python and Streamlit application that converts
synthetic life-insurance reference documents into structured, reviewable product
records. It combines document ingestion, OCR, deterministic field extraction,
grounded question answering, validation, analytics, and SQLite audit logging in
one transparent workflow.

**Created by Arkamitra Bhattacharyya.**

> All bundled insurers, products, limits, and terms are fictitious. PolicyLens
> is a technical demonstration, not financial advice and not a representation
> of Munich Re or any insurer.

## What the application demonstrates

| Capability | Implementation | Business value |
|---|---|---|
| Document ingestion | Markdown, text, native PDF, and image/PDF OCR fallback | Handles inconsistent reference formats |
| Product structuring | Extracts common cover, age, benefit, premium, and exclusion fields | Reduces manual reference preparation |
| Validation | Required-field and range checks with a visible review queue | Prevents silent downstream data-quality failures |
| Grounded Q&A | TF-IDF retrieval, source citations, and weak-evidence abstention | Keeps answers inspectable |
| Optional GenAI | OpenAI synthesis restricted to retrieved evidence | Adds concise synthesis without removing controls |
| Analytics dashboard | Coverage, readiness, product limits, waiting periods, and audit KPIs | Gives stakeholders an operational view |
| Audit trail | SQLite records for document-processing and Q&A events | Supports traceability and review |
| Delivery quality | Automated tests, GitHub Actions, Docker, and Streamlit configuration | Makes the demo reproducible and deployable |

## Architecture

```mermaid
flowchart TD
    A[PDF, image, or text] --> B[Text extraction and OCR]
    B --> C[Page-aware evidence chunks]
    C --> D[Structured field extraction]
    D --> E[Validation and review queue]
    C --> F[Grounded retrieval]
    F --> G[Extractive or optional LLM answer]
    D --> H[Analytics dashboard]
    E --> I[(SQLite audit log)]
    G --> I
```

The deterministic extraction and retrieval path works without an API key. An
LLM is used only when the user explicitly enables synthesis and supplies a key.

## Dashboard

After documents are processed, the **Analytics dashboard** provides:

- readiness rate and average extraction confidence;
- maximum sum insured by product;
- field-level evidence coverage;
- waiting-period availability across products;
- validation exceptions and review gaps;
- audited Q&A volume; and
- a downloadable dashboard dataset in CSV format.

The dashboard can be filtered by provider and review status.

## Quick start

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`, select **Load three synthetic products**, and try:

```text
Which product offers a 30-day waiting period?
```

## Optional OCR support

The text and PDF demo works without a system OCR package. Image OCR also
requires the Tesseract executable:

```bash
# macOS with Homebrew
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

Use `data/sample/scanned_demo.png` to demonstrate the OCR path.

## Optional grounded LLM mode

The default answerer runs locally. To enable evidence-constrained OpenAI
synthesis, copy the environment template and add a key:

```bash
cp .env.example .env
```

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5-mini
```

The `.env` file is excluded from Git and must never be committed. In the app,
enable **Use optional LLM synthesis** after loading documents.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/run_demo.py
```

The test suite covers extraction, validation, citations, deduplication,
persistence, weak-evidence abstention, and dashboard summaries. GitHub Actions
runs the suite on Python 3.11 and 3.12 for every push and pull request to `main`.

## Publish this project to GitHub

1. On GitHub, create a public repository named `policylens`.
2. Do **not** initialise it with another README, `.gitignore`, or licence because
   this project already includes them.
3. From the PolicyLens folder, run:

```bash
git init
git add .
git commit -m "Initial release of PolicyLens"
git branch -M main
git remote add origin REPLACE_WITH_YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Copy the repository URL shown on GitHub and replace
`REPLACE_WITH_YOUR_GITHUB_REPOSITORY_URL`. GitHub's
official repository-creation guide is available at
<https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository>.

Suggested repository description:

> Evidence-first Streamlit workbench for OCR, structured insurance-product
> extraction, grounded Q&A, analytics, validation, and audit logging.

Suggested topics: `streamlit`, `python`, `ocr`, `llm`, `rag`, `insurance`,
`document-intelligence`, `responsible-ai`, `sqlite`, `data-analytics`.

## Deploy on Streamlit Community Cloud

Once the repository is on GitHub:

1. Sign in to <https://share.streamlit.io> with GitHub.
2. Select **Create app**.
3. Choose the `policylens` repository and the `main` branch.
4. Set the main file path to `app.py`.
5. Add `OPENAI_API_KEY` and `OPENAI_MODEL` under advanced secrets only if LLM
   mode is required.
6. Select **Deploy**.

See Streamlit's official deployment guide at
<https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app>.

## Docker

```bash
docker build -t policylens .
docker run --rm -p 8501:8501 policylens
```

Then open `http://localhost:8501`.

## Repository structure

```text
PolicyLens/
├── .github/workflows/ci.yml       # Automated tests
├── .streamlit/config.toml         # UI and server configuration
├── app.py                         # Streamlit interface and dashboard
├── data/sample/                   # Synthetic product references and OCR image
├── docs/policylens-banner.svg     # GitHub README banner
├── scripts/run_demo.py            # Offline end-to-end demonstration
├── src/policylens/
│   ├── agents.py                  # Workflow coordination
│   ├── analytics.py               # Dashboard-ready summaries
│   ├── audit.py                   # SQLite persistence
│   ├── extract.py                 # Field extraction and validation
│   ├── ingest.py                  # PDF, text, and OCR ingestion
│   ├── llm.py                     # Optional grounded LLM synthesis
│   ├── models.py                  # Domain models
│   └── retrieval.py               # Retrieval and citations
├── tests/test_policylens.py       # Automated workflow tests
├── Dockerfile                     # Container deployment
├── LICENSE                        # MIT licence
└── requirements.txt               # Runtime dependencies
```

## Design decisions to discuss in an interview

1. **Deterministic core:** the main demo remains reliable, explainable, and
   inexpensive; an LLM is used only where synthesis adds value.
2. **Evidence retention:** page-aware chunks preserve provenance for analysts,
   actuaries, and reviewers.
3. **Visible failures:** missing or contradictory values become review tasks
   instead of plausible-looking guesses.
4. **Human-in-the-loop:** extracted values remain drafts until a reviewer checks
   them against the cited source.
5. **Scalable path:** local files, SQLite, in-memory retrieval, and synchronous
   processing can be replaced by object storage, a managed database, a vector
   index, and queued workers.

## Responsible-use boundaries

- Do not upload confidential, personal, or commercially sensitive information
  to a public deployment.
- Treat extracted values as draft reference data until reviewed.
- Do not use the application for underwriting, claims decisions, financial
  advice, or automated eligibility decisions.
- Use licensed and approved source documents in a real deployment.

## Licence

MIT © 2026 Arkamitra Bhattacharyya.
