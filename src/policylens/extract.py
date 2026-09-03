"""Deterministic product-field extraction and quality checks."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import ProductRecord, SourceChunk


FIELD_PATTERNS = {
    "product_name": r"Product Name\s*:\s*([^\n]+)",
    "provider": r"Provider\s*:\s*([^\n]+)",
    "cover_types": r"Cover Types?\s*:\s*([^\n]+)",
    "entry_age": r"Entry Age\s*:\s*(\d{1,2})\s*(?:to|-)\s*(\d{1,2})",
    "expiry_age": r"Expiry Age\s*:\s*(\d{1,3})",
    "sum_insured": (
        r"Sum Insured\s*:\s*AUD\s*\$?([\d,]+)\s*(?:to|-)\s*"
        r"AUD\s*\$?([\d,]+)"
    ),
    "waiting_period": r"Waiting Periods?\s*:\s*([^\n]+)",
    "benefit_period": r"Benefit Period\s*:\s*([^\n]+)",
    "premium_structure": r"Premium Structure\s*:\s*([^\n]+)",
    "exclusions": r"Key Exclusions?\s*:\s*([^\n]+)",
}


class ProductExtractor:
    """Extract a compact product schema from semi-structured reference text."""

    REQUIRED_FIELDS = (
        "product_name",
        "provider",
        "cover_types",
        "minimum_entry_age",
        "maximum_entry_age",
        "expiry_age",
        "minimum_sum_insured_aud",
        "maximum_sum_insured_aud",
        "premium_structure",
    )

    def extract(
        self,
        document_id: str,
        source_name: str,
        chunks: Iterable[SourceChunk],
    ) -> ProductRecord:
        full_text = "\n".join(chunk.text for chunk in chunks)
        record = ProductRecord(document_id=document_id, source_name=source_name)

        record.product_name = self._single(full_text, "product_name")
        record.provider = self._single(full_text, "provider")

        covers = self._single(full_text, "cover_types")
        if covers:
            record.cover_types = self._list(covers)

        entry_match = self._match(full_text, "entry_age")
        if entry_match:
            record.minimum_entry_age = int(entry_match.group(1))
            record.maximum_entry_age = int(entry_match.group(2))

        expiry = self._single(full_text, "expiry_age")
        if expiry:
            record.expiry_age = int(expiry)

        sum_match = self._match(full_text, "sum_insured")
        if sum_match:
            record.minimum_sum_insured_aud = self._money(sum_match.group(1))
            record.maximum_sum_insured_aud = self._money(sum_match.group(2))

        waiting = self._single(full_text, "waiting_period")
        if waiting:
            record.waiting_period_days = [int(x) for x in re.findall(r"\d+", waiting)]

        record.benefit_period = self._single(full_text, "benefit_period")
        record.premium_structure = self._single(full_text, "premium_structure")

        exclusions = self._single(full_text, "exclusions")
        if exclusions:
            record.key_exclusions = self._list(exclusions)

        self.validate(record)
        return record

    def validate(self, record: ProductRecord) -> ProductRecord:
        notes: list[str] = []
        present = 0
        for field_name in self.REQUIRED_FIELDS:
            value = getattr(record, field_name)
            if value not in (None, "", []):
                present += 1
            else:
                notes.append(f"Missing required field: {field_name.replace('_', ' ')}")

        if (
            record.minimum_entry_age is not None
            and record.maximum_entry_age is not None
            and record.minimum_entry_age > record.maximum_entry_age
        ):
            notes.append("Minimum entry age exceeds maximum entry age")

        if (
            record.minimum_sum_insured_aud is not None
            and record.maximum_sum_insured_aud is not None
            and record.minimum_sum_insured_aud > record.maximum_sum_insured_aud
        ):
            notes.append("Minimum sum insured exceeds maximum sum insured")

        record.confidence = present / len(self.REQUIRED_FIELDS)
        record.validation_notes = notes
        record.review_status = "Ready" if not notes else "Needs review"
        return record

    @staticmethod
    def _list(value: str) -> list[str]:
        return [item.strip(" .") for item in re.split(r"[,;]", value) if item.strip()]

    @staticmethod
    def _money(value: str) -> int:
        return int(value.replace(",", ""))

    @staticmethod
    def _match(text: str, field: str):
        return re.search(FIELD_PATTERNS[field], text, flags=re.IGNORECASE)

    def _single(self, text: str, field: str) -> str | None:
        match = self._match(text, field)
        return match.group(1).strip(" .") if match else None
