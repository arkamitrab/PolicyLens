"""Agent-style orchestration for ingestion, extraction, validation, and Q&A."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .audit import AuditRepository
from .extract import ProductExtractor
from .ingest import DocumentIngestor, PageText, chunk_pages
from .llm import answer_with_openai
from .models import ProductRecord, SourceChunk
from .retrieval import GroundedAnswer, GroundedRetriever


@dataclass(slots=True)
class ProcessedDocument:
    product: ProductRecord
    pages: list[PageText]
    chunks: list[SourceChunk]


class PolicyWorkflow:
    """Coordinate specialised stages and preserve evidence across the workflow."""

    def __init__(self, audit_path: str = "policylens.db"):
        self.ingestor = DocumentIngestor()
        self.extractor = ProductExtractor()
        self.retriever = GroundedRetriever()
        self.audit = AuditRepository(audit_path)

    def process_bytes(self, filename: str, content: bytes) -> ProcessedDocument:
        document_id = hashlib.sha256(content).hexdigest()[:16]
        pages = self.ingestor.ingest_bytes(filename, content)
        chunks = list(chunk_pages(document_id, filename, pages))
        product = self.extractor.extract(document_id, filename, chunks)
        self.retriever.add(chunks)
        self.audit.save_document(product, [page.extraction_method for page in pages])
        return ProcessedDocument(product=product, pages=pages, chunks=chunks)

    def ask(self, question: str, use_llm: bool = False, top_k: int = 3) -> GroundedAnswer:
        hits = self.retriever.search(question, top_k=top_k)
        hits = self.retriever.relevant_hits(hits)
        answer = answer_with_openai(question, hits) if use_llm else None
        if answer is None:
            answer = self.retriever.answer(question, top_k=top_k)
        self.audit.save_question(question, answer.answer, answer.citations, answer.mode)
        return answer
