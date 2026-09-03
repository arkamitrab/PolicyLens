"""Optional LLM synthesis that is constrained to retrieved evidence."""

from __future__ import annotations

import os

from .retrieval import GroundedAnswer, RetrievalHit


def answer_with_openai(question: str, hits: list[RetrievalHit]) -> GroundedAnswer | None:
    """Return a grounded LLM answer, or None when optional dependencies are absent."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not hits:
        return None
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover - optional deployment feature
        return None

    evidence = "\n\n".join(
        f"SOURCE [{hit.chunk.citation}]\n{hit.chunk.text}" for hit in hits
    )
    instructions = (
        "You answer questions about synthetic insurance product documents. "
        "Use only the supplied evidence. If it is insufficient, say so. "
        "Add bracketed source citations exactly as provided. Do not provide "
        "financial advice or infer missing policy terms."
    )
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        instructions=instructions,
        input=f"Question: {question}\n\nEvidence:\n{evidence}",
    )
    citations = list(dict.fromkeys(hit.chunk.citation for hit in hits))
    return GroundedAnswer(
        answer=response.output_text,
        citations=citations,
        hits=hits,
        mode="llm-grounded",
    )
