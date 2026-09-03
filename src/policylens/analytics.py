"""Dashboard-ready summaries for processed policy records."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .models import ProductRecord


DASHBOARD_FIELDS = (
    ("Product name", "product_name"),
    ("Provider", "provider"),
    ("Cover types", "cover_types"),
    ("Entry age", "minimum_entry_age"),
    ("Expiry age", "expiry_age"),
    ("Minimum sum insured", "minimum_sum_insured_aud"),
    ("Maximum sum insured", "maximum_sum_insured_aud"),
    ("Waiting period", "waiting_period_days"),
    ("Benefit period", "benefit_period"),
    ("Premium structure", "premium_structure"),
    ("Key exclusions", "key_exclusions"),
)


def product_dashboard_rows(products: Iterable[ProductRecord]) -> list[dict]:
    """Return one numeric, chart-friendly row per product."""
    rows = []
    for product in products:
        rows.append(
            {
                "Product": product.product_name or product.source_name,
                "Provider": product.provider or "Not found",
                "Status": product.review_status,
                "Confidence (%)": round(product.confidence * 100, 1),
                "Minimum sum insured (AUD)": product.minimum_sum_insured_aud,
                "Maximum sum insured (AUD)": product.maximum_sum_insured_aud,
                "Waiting-period options": len(product.waiting_period_days),
                "Exclusions captured": len(product.key_exclusions),
                "Validation issues": len(product.validation_notes),
            }
        )
    return rows


def field_coverage(products: Iterable[ProductRecord]) -> list[dict]:
    """Calculate the percentage of records with evidence for each field."""
    records = list(products)
    if not records:
        return []
    return [
        {
            "Field": label,
            "Coverage (%)": round(
                100 * sum(_is_present(getattr(record, attribute)) for record in records)
                / len(records),
                1,
            ),
        }
        for label, attribute in DASHBOARD_FIELDS
    ]


def waiting_period_distribution(products: Iterable[ProductRecord]) -> list[dict]:
    """Count how many products offer each waiting-period option."""
    counts = Counter(
        period
        for product in products
        for period in set(product.waiting_period_days)
    )
    return [
        {"Waiting period (days)": period, "Products": counts[period]}
        for period in sorted(counts)
    ]


def review_issue_rows(products: Iterable[ProductRecord]) -> list[dict]:
    """Flatten validation notes for a reviewer-facing exception table."""
    return [
        {
            "Product": product.product_name or product.source_name,
            "Issue": note,
        }
        for product in products
        for note in product.validation_notes
    ]


def _is_present(value: object) -> bool:
    return value not in (None, "", [])
