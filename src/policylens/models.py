"""Domain models shared across the PolicyLens pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceChunk:
    document_id: str
    source_name: str
    page: int
    chunk_id: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source_name}, p. {self.page}"


@dataclass(slots=True)
class ProductRecord:
    document_id: str
    source_name: str
    product_name: str | None = None
    provider: str | None = None
    cover_types: list[str] = field(default_factory=list)
    minimum_entry_age: int | None = None
    maximum_entry_age: int | None = None
    expiry_age: int | None = None
    minimum_sum_insured_aud: int | None = None
    maximum_sum_insured_aud: int | None = None
    waiting_period_days: list[int] = field(default_factory=list)
    benefit_period: str | None = None
    premium_structure: str | None = None
    key_exclusions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    review_status: str = "Needs review"
    validation_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def comparison_row(self) -> dict[str, Any]:
        return {
            "Product": self.product_name or "Not found",
            "Provider": self.provider or "Not found",
            "Cover": ", ".join(self.cover_types) or "Not found",
            "Entry age": _age_range(self.minimum_entry_age, self.maximum_entry_age),
            "Expiry age": self.expiry_age or "Not found",
            "Sum insured": _money_range(
                self.minimum_sum_insured_aud, self.maximum_sum_insured_aud
            ),
            "Waiting period": (
                ", ".join(f"{x} days" for x in self.waiting_period_days)
                or "Not found"
            ),
            "Benefit period": self.benefit_period or "Not found",
            "Premium": self.premium_structure or "Not found",
            "Confidence": f"{self.confidence:.0%}",
            "Status": self.review_status,
        }


def _age_range(low: int | None, high: int | None) -> str:
    if low is None and high is None:
        return "Not found"
    if low is None:
        return f"Up to {high}"
    if high is None:
        return f"From {low}"
    return f"{low}-{high}"


def _money_range(low: int | None, high: int | None) -> str:
    def fmt(value: int | None) -> str:
        return f"${value:,.0f}" if value is not None else "?"

    if low is None and high is None:
        return "Not found"
    return f"{fmt(low)}-{fmt(high)}"
