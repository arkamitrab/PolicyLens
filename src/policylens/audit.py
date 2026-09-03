"""SQLite audit trail for document processing and Q&A events."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import ProductRecord


class AuditRepository:
    def __init__(self, path: str | Path = "policylens.db"):
        self.path = str(path)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS document_runs (
                    document_id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    extraction_methods TEXT NOT NULL,
                    product_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    review_status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS question_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    answer_mode TEXT NOT NULL
                );
                """
            )

    def save_document(self, product: ProductRecord, methods: list[str]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO document_runs (
                    document_id, source_name, extraction_methods, product_json,
                    confidence, review_status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    source_name=excluded.source_name,
                    processed_at=CURRENT_TIMESTAMP,
                    extraction_methods=excluded.extraction_methods,
                    product_json=excluded.product_json,
                    confidence=excluded.confidence,
                    review_status=excluded.review_status
                """,
                (
                    product.document_id,
                    product.source_name,
                    json.dumps(methods),
                    json.dumps(product.to_dict()),
                    product.confidence,
                    product.review_status,
                ),
            )

    def save_question(
        self, question: str, answer: str, citations: list[str], mode: str
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO question_runs (question, answer, citations_json, answer_mode)
                VALUES (?, ?, ?, ?)
                """,
                (question, answer, json.dumps(citations), mode),
            )

    def recent_documents(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_name, processed_at, confidence, review_status,
                       extraction_methods
                FROM document_runs ORDER BY processed_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def recent_questions(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT asked_at, question, answer_mode, citations_json
                FROM question_runs ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
