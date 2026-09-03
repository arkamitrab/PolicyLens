"""Transparent retrieval and citation-grounded answers."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .models import SourceChunk


@dataclass(slots=True)
class RetrievalHit:
    chunk: SourceChunk
    score: float


@dataclass(slots=True)
class GroundedAnswer:
    answer: str
    citations: list[str]
    hits: list[RetrievalHit]
    mode: str = "extractive"


class GroundedRetriever:
    """Rank chunks using TF-IDF when available, with a token-overlap fallback."""

    def __init__(self, chunks: list[SourceChunk] | None = None):
        self.chunks = chunks or []

    def add(self, chunks: list[SourceChunk]) -> None:
        existing = {chunk.chunk_id for chunk in self.chunks}
        self.chunks.extend(chunk for chunk in chunks if chunk.chunk_id not in existing)

    def search(self, question: str, top_k: int = 3) -> list[RetrievalHit]:
        if not self.chunks or not question.strip():
            return []
        try:
            return self._tfidf(question, top_k)
        except (ImportError, ValueError):
            return self._token_overlap(question, top_k)

    def answer(self, question: str, top_k: int = 3) -> GroundedAnswer:
        hits = self.search(question, top_k)
        if not hits or hits[0].score <= 0:
            return GroundedAnswer(
                answer="I could not find enough evidence in the uploaded documents.",
                citations=[],
                hits=hits,
            )

        hits = self.relevant_hits(hits)

        sentences: list[str] = []
        for hit in hits:
            # Treat structured field lines as answer candidates as well as prose
            # sentences, so an exact value beats a nearby narrative paragraph.
            candidates = re.split(r"(?<=[.!?])\s+|\n+", hit.chunk.text)
            best = max(
                candidates,
                key=lambda sentence: self._overlap_score(question, sentence),
                default=hit.chunk.text,
            )
            cleaned = best.strip()
            product_match = re.search(
                r"Product Name\s*:\s*([^\n]+)", hit.chunk.text, flags=re.IGNORECASE
            )
            if product_match and "which product" in question.lower():
                cleaned = f"{product_match.group(1).strip()}: {cleaned}"
            if cleaned and cleaned not in sentences:
                sentences.append(cleaned)

        citations = list(dict.fromkeys(hit.chunk.citation for hit in hits))
        answer = " ".join(sentences[:3])
        return GroundedAnswer(answer=answer, citations=citations, hits=hits)

    @staticmethod
    def relevant_hits(hits: list[RetrievalHit], relative_cutoff: float = 0.65):
        """Remove weak tail results while retaining ties near the best evidence."""
        if not hits:
            return []
        threshold = hits[0].score * relative_cutoff
        return [hit for hit in hits if hit.score >= threshold and hit.score > 0]

    def _tfidf(self, question: str, top_k: int) -> list[RetrievalHit]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        corpus = [chunk.text for chunk in self.chunks]
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(
            corpus + [question]
        )
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        return [
            RetrievalHit(self.chunks[index], float(score))
            for index, score in ranked[:top_k]
        ]

    def _token_overlap(self, question: str, top_k: int) -> list[RetrievalHit]:
        ranked = [
            RetrievalHit(chunk, self._overlap_score(question, chunk.text))
            for chunk in self.chunks
        ]
        return sorted(ranked, key=lambda hit: hit.score, reverse=True)[:top_k]

    @staticmethod
    def _overlap_score(left: str, right: str) -> float:
        left_tokens = set(re.findall(r"[a-z0-9]+", left.lower()))
        right_tokens = set(re.findall(r"[a-z0-9]+", right.lower()))
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / math.sqrt(
            len(left_tokens) * len(right_tokens)
        )
