"""Run the core workflow without Streamlit and print a recruiter-friendly demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from policylens import PolicyWorkflow


def main() -> None:
    audit_path = ROOT / "demo_audit.db"
    workflow = PolicyWorkflow(str(audit_path))
    products = []
    for path in sorted((ROOT / "data" / "sample").glob("*.md")):
        result = workflow.process_bytes(path.name, path.read_bytes())
        products.append(result.product.comparison_row())

    answer = workflow.ask("Which product offers a 30-day waiting period?")
    print(json.dumps({"products": products, "answer": answer.answer,
                      "citations": answer.citations}, indent=2))


if __name__ == "__main__":
    main()
