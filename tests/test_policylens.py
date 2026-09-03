from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from policylens.agents import PolicyWorkflow
from policylens.analytics import (
    field_coverage,
    product_dashboard_rows,
    waiting_period_distribution,
)
from policylens.audit import AuditRepository


ROOT = Path(__file__).resolve().parents[1]


class PolicyLensTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        self.workflow = PolicyWorkflow(str(self.db_path))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_extracts_expected_product_fields(self):
        sample = ROOT / "data" / "sample" / "02_southern_horizon_income_protection.md"
        result = self.workflow.process_bytes(sample.name, sample.read_bytes())
        product = result.product
        self.assertEqual(product.product_name, "Southern Horizon Income Protection")
        self.assertEqual(product.minimum_entry_age, 18)
        self.assertEqual(product.maximum_entry_age, 59)
        self.assertEqual(product.waiting_period_days, [30, 60, 90])
        self.assertEqual(product.maximum_sum_insured_aud, 30000)
        self.assertEqual(product.review_status, "Ready")
        self.assertEqual(product.confidence, 1.0)

    def test_grounded_answer_includes_source(self):
        for sample in sorted((ROOT / "data" / "sample").glob("*.md")):
            self.workflow.process_bytes(sample.name, sample.read_bytes())
        answer = self.workflow.ask("Which product offers a 30-day waiting period?")
        self.assertIn("30", answer.answer)
        self.assertIn("Southern Horizon Income Protection", answer.answer)
        self.assertTrue(any("southern_horizon" in item for item in answer.citations))

    def test_audit_repository_records_events(self):
        sample = ROOT / "data" / "sample" / "01_harbourlife_secure_term.md"
        self.workflow.process_bytes(sample.name, sample.read_bytes())
        self.workflow.ask("What is the maximum sum insured?")
        audit = AuditRepository(self.db_path)
        self.assertEqual(len(audit.recent_documents()), 1)
        self.assertEqual(len(audit.recent_questions()), 1)

    def test_duplicate_document_does_not_duplicate_chunks(self):
        sample = ROOT / "data" / "sample" / "01_harbourlife_secure_term.md"
        for _ in range(2):
            self.workflow.process_bytes(sample.name, sample.read_bytes())
        chunk_ids = [chunk.chunk_id for chunk in self.workflow.retriever.chunks]
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))

    def test_incomplete_record_is_sent_to_review(self):
        content = b"Product Name: Incomplete Demo\nProvider: Fictional Provider"
        result = self.workflow.process_bytes("incomplete.txt", content)
        self.assertEqual(result.product.review_status, "Needs review")
        self.assertLess(result.product.confidence, 1.0)
        self.assertTrue(result.product.validation_notes)

    def test_weak_evidence_causes_abstention(self):
        sample = ROOT / "data" / "sample" / "01_harbourlife_secure_term.md"
        self.workflow.process_bytes(sample.name, sample.read_bytes())
        answer = self.workflow.ask("Explain quantum chromodynamics and gluon colour charge.")
        self.assertIn("could not find enough evidence", answer.answer.lower())

    def test_dashboard_summaries_are_chart_ready(self):
        products = []
        for sample in sorted((ROOT / "data" / "sample").glob("*.md")):
            products.append(
                self.workflow.process_bytes(sample.name, sample.read_bytes()).product
            )

        rows = product_dashboard_rows(products)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["Confidence (%)"] == 100 for row in rows))

        coverage = field_coverage(products)
        self.assertEqual(len(coverage), 11)
        self.assertTrue(all(row["Coverage (%)"] == 100 for row in coverage))

        waiting = waiting_period_distribution(products)
        self.assertEqual(
            waiting,
            [
                {"Waiting period (days)": 0, "Products": 1},
                {"Waiting period (days)": 30, "Products": 1},
                {"Waiting period (days)": 60, "Products": 1},
                {"Waiting period (days)": 90, "Products": 2},
            ],
        )


if __name__ == "__main__":
    unittest.main()
