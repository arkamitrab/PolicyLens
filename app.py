"""PolicyLens Streamlit application."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "src"))

from policylens import PolicyWorkflow  # noqa: E402
from policylens.analytics import (  # noqa: E402
    field_coverage,
    product_dashboard_rows,
    review_issue_rows,
    waiting_period_distribution,
)


st.set_page_config(page_title="PolicyLens", page_icon="🔎", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1250px;}
    .hero {padding: 1.25rem 1.4rem; border-radius: 16px;
      background: linear-gradient(120deg,#071f3a,#0b6b68); color:white; margin-bottom:1rem;}
    .hero h1 {margin:0; font-size:2.15rem;}
    .hero p {margin:.35rem 0 0; opacity:.9;}
    .hero .byline {display:inline-block; margin-top:.7rem; font-size:.86rem;
      letter-spacing:.02em; opacity:.78;}
    .note {border-left:4px solid #20a39e; padding:.6rem .9rem; background:#f2fbfa;}
    .footer {text-align:center; color:#62707c; font-size:.82rem; padding:1rem 0 .25rem;}
    </style>
    <div class="hero">
      <h1>PolicyLens</h1>
      <p>Evidence-first document intelligence for life-insurance product teams.</p>
      <span class="byline">Created by Arkamitra Bhattacharyya</span>
    </div>
    """,
    unsafe_allow_html=True,
)


def initialise_state() -> None:
    if "workflow" not in st.session_state:
        st.session_state.workflow = PolicyWorkflow(str(ROOT / "policylens.db"))
    if "processed" not in st.session_state:
        st.session_state.processed = {}


def process_file(filename: str, content: bytes) -> None:
    result = st.session_state.workflow.process_bytes(filename, content)
    st.session_state.processed[result.product.document_id] = result


initialise_state()

with st.sidebar:
    st.header("Demo controls")
    if st.button("Load three synthetic products", width="stretch"):
        for path in sorted((ROOT / "data" / "sample").glob("*.md")):
            process_file(path.name, path.read_bytes())
        st.success("Sample portfolio loaded.")

    uploads = st.file_uploader(
        "Upload reference documents",
        type=["pdf", "txt", "md", "png", "jpg", "jpeg", "tif", "tiff"],
        accept_multiple_files=True,
    )
    if uploads and st.button("Process uploads", type="primary", width="stretch"):
        processed_count = 0
        for uploaded in uploads:
            try:
                process_file(uploaded.name, uploaded.getvalue())
                processed_count += 1
            except (RuntimeError, ValueError) as exc:
                st.error(f"Could not process {uploaded.name}: {exc}")
        if processed_count:
            st.success(f"Processed {processed_count} document(s).")

    use_llm = st.toggle(
        "Use optional LLM synthesis",
        value=False,
        help="Requires OPENAI_API_KEY. Retrieval and citations still run locally.",
    )
    if shutil.which("tesseract"):
        st.success("OCR engine ready", icon="✅")
    else:
        st.warning(
            "OCR engine unavailable. Native PDF and text ingestion still work.",
            icon="⚠️",
        )
    st.caption("Synthetic demonstration only — not financial advice.")

processed = list(st.session_state.processed.values())
products = [item.product for item in processed]

overview, dashboard, compare, ask, review = st.tabs(
    [
        "Portfolio overview",
        "Analytics dashboard",
        "Product comparison",
        "Grounded Q&A",
        "Review & audit",
    ]
)

with overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents", len(products))
    col2.metric("Ready records", sum(p.review_status == "Ready" for p in products))
    average_confidence = sum(p.confidence for p in products) / len(products) if products else 0
    col3.metric("Mean field coverage", f"{average_confidence:.0%}")
    col4.metric("Evidence chunks", sum(len(item.chunks) for item in processed))

    st.subheader("How it works")
    st.markdown(
        """
        1. **Ingest** embedded text or apply OCR to scanned pages.
        2. **Structure** common product terms into a reviewable schema.
        3. **Validate** missing or inconsistent fields before downstream use.
        4. **Retrieve and answer** from source chunks with page citations.
        5. **Audit** processing and Q&A events in SQLite.
        """
    )
    if not products:
        st.info("Load the synthetic portfolio from the sidebar or upload a document.")
    else:
        st.dataframe(
            pd.DataFrame([p.comparison_row() for p in products]),
            width="stretch",
            hide_index=True,
        )

with dashboard:
    st.subheader("Portfolio analytics dashboard")
    if not products:
        st.info("Load the synthetic portfolio or process documents to populate the dashboard.")
    else:
        dashboard_frame = pd.DataFrame(product_dashboard_rows(products))
        provider_options = sorted(dashboard_frame["Provider"].unique())
        status_options = sorted(dashboard_frame["Status"].unique())

        filter_col1, filter_col2 = st.columns(2)
        selected_providers = filter_col1.multiselect(
            "Provider",
            provider_options,
            default=provider_options,
        )
        selected_statuses = filter_col2.multiselect(
            "Review status",
            status_options,
            default=status_options,
        )
        filtered = dashboard_frame[
            dashboard_frame["Provider"].isin(selected_providers)
            & dashboard_frame["Status"].isin(selected_statuses)
        ]

        if filtered.empty:
            st.warning("No products match the selected dashboard filters.")
        else:
            filtered_names = set(filtered["Product"])
            filtered_products = [
                product
                for product in products
                if (product.product_name or product.source_name) in filtered_names
            ]
            question_events = st.session_state.workflow.audit.recent_questions(limit=100)
            ready_count = int((filtered["Status"] == "Ready").sum())

            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Products in view", len(filtered))
            metric2.metric("Ready for use", f"{ready_count / len(filtered):.0%}")
            metric3.metric("Mean field confidence", f"{filtered['Confidence (%)'].mean():.0f}%")
            metric4.metric("Questions audited", len(question_events))

            chart_left, chart_right = st.columns(2)
            with chart_left:
                st.markdown("#### Maximum sum insured")
                cover_frame = filtered[["Product", "Maximum sum insured (AUD)"]].dropna()
                st.bar_chart(
                    cover_frame,
                    x="Product",
                    y="Maximum sum insured (AUD)",
                    color="#0b6b68",
                    width="stretch",
                )
            with chart_right:
                st.markdown("#### Extracted-field coverage")
                coverage_frame = pd.DataFrame(field_coverage(filtered_products))
                st.bar_chart(
                    coverage_frame,
                    x="Field",
                    y="Coverage (%)",
                    color="#2878a8",
                    width="stretch",
                )

            detail_left, detail_right = st.columns(2)
            with detail_left:
                st.markdown("#### Waiting-period availability")
                waiting_frame = pd.DataFrame(
                    waiting_period_distribution(filtered_products)
                )
                if waiting_frame.empty:
                    st.caption("No waiting-period values were extracted.")
                else:
                    st.bar_chart(
                        waiting_frame,
                        x="Waiting period (days)",
                        y="Products",
                        color="#e58b3a",
                        width="stretch",
                    )
            with detail_right:
                st.markdown("#### Validation exceptions")
                issue_frame = pd.DataFrame(review_issue_rows(filtered_products))
                if issue_frame.empty:
                    st.success("No validation exceptions in the current view.")
                else:
                    st.dataframe(issue_frame, width="stretch", hide_index=True)

            st.markdown("#### Ingestion methods")
            filtered_ids = {product.document_id for product in filtered_products}
            methods = [
                page.extraction_method
                for item in processed
                if item.product.document_id in filtered_ids
                for page in item.pages
            ]
            method_frame = (
                pd.Series(methods, name="Method")
                .value_counts()
                .rename_axis("Method")
                .reset_index(name="Pages")
            )
            st.bar_chart(
                method_frame,
                x="Method",
                y="Pages",
                color="#7c5ce7",
                width="stretch",
            )

            st.markdown("#### Dashboard data")
            st.dataframe(filtered, width="stretch", hide_index=True)
            st.download_button(
                "Download dashboard data",
                filtered.to_csv(index=False),
                file_name="policylens_dashboard.csv",
                mime="text/csv",
            )

with compare:
    st.subheader("Side-by-side product reference")
    if len(products) < 2:
        st.info("Load at least two products to compare terms.")
    else:
        frame = pd.DataFrame([p.comparison_row() for p in products])
        st.dataframe(frame, width="stretch", hide_index=True)
        st.download_button(
            "Download comparison CSV",
            frame.to_csv(index=False),
            file_name="policylens_comparison.csv",
            mime="text/csv",
        )

with ask:
    st.subheader("Ask across the reference set")
    st.markdown(
        '<div class="note">Answers must be supported by retrieved source text. '
        "When evidence is weak, the system abstains.</div>",
        unsafe_allow_html=True,
    )
    question = st.text_input(
        "Question",
        placeholder="Which product includes a 30-day waiting-period option?",
    )
    if st.button("Find grounded answer", type="primary", disabled=not products):
        answer = st.session_state.workflow.ask(question, use_llm=use_llm)
        st.markdown(answer.answer)
        if answer.citations:
            st.caption("Sources: " + "; ".join(answer.citations))
        st.caption(f"Answer mode: {answer.mode}")
        with st.expander("Inspect retrieved evidence"):
            for hit in answer.hits:
                st.markdown(f"**{hit.chunk.citation} — relevance {hit.score:.3f}**")
                st.write(hit.chunk.text)

with review:
    st.subheader("Human review queue")
    if not products:
        st.info("No records have been processed.")
    for product in products:
        label = f"{product.product_name or product.source_name} — {product.review_status}"
        with st.expander(label):
            left, right = st.columns([2, 1])
            left.json(product.to_dict(), expanded=True)
            right.metric("Field coverage", f"{product.confidence:.0%}")
            right.write("Validation notes")
            if product.validation_notes:
                for note in product.validation_notes:
                    right.warning(note)
            else:
                right.success("All required fields were detected.")

    st.subheader("Recent processing events")
    document_runs = st.session_state.workflow.audit.recent_documents()
    if document_runs:
        for row in document_runs:
            row["extraction_methods"] = ", ".join(json.loads(row["extraction_methods"]))
        st.dataframe(pd.DataFrame(document_runs), width="stretch", hide_index=True)

    st.subheader("Recent grounded questions")
    question_runs = st.session_state.workflow.audit.recent_questions()
    if not question_runs:
        st.caption("No questions have been recorded in this session yet.")
    else:
        for row in question_runs:
            row["citations"] = ", ".join(json.loads(row.pop("citations_json")))
        st.dataframe(pd.DataFrame(question_runs), width="stretch", hide_index=True)

st.markdown(
    '<div class="footer">Created by Arkamitra Bhattacharyya · '
    "Synthetic portfolio demonstration only</div>",
    unsafe_allow_html=True,
)
