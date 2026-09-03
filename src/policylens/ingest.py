"""Text and OCR ingestion with page-level provenance."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PageText:
    page: int
    text: str
    extraction_method: str


class DocumentIngestor:
    """Extract text from TXT/MD, PDF, or common image formats.

    PDF text extraction uses PyMuPDF. If a PDF page has little embedded text,
    or an image is uploaded, pytesseract is used when available.
    """

    TEXT_EXTENSIONS = {".txt", ".md"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    def ingest_path(self, path: str | Path) -> list[PageText]:
        source = Path(path)
        return self.ingest_bytes(source.name, source.read_bytes())

    def ingest_bytes(self, filename: str, content: bytes) -> list[PageText]:
        suffix = Path(filename).suffix.lower()
        if suffix in self.TEXT_EXTENSIONS:
            text = content.decode("utf-8", errors="replace")
            return [PageText(page=1, text=text, extraction_method="native-text")]
        if suffix == ".pdf":
            return self._ingest_pdf(content)
        if suffix in self.IMAGE_EXTENSIONS:
            return [
                PageText(page=1, text=self._ocr_image(content), extraction_method="ocr")
            ]
        raise ValueError(
            f"Unsupported file type '{suffix}'. Use PDF, TXT, MD, PNG, JPG, or TIFF."
        )

    def _ingest_pdf(self, content: bytes) -> list[PageText]:
        try:
            import fitz
        except ImportError as exc:  # pragma: no cover - depends on deployment
            raise RuntimeError("PDF support requires PyMuPDF.") from exc

        pages: list[PageText] = []
        with fitz.open(stream=content, filetype="pdf") as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                method = "pdf-text"
                if len(text) < 40:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    text = self._ocr_image(pixmap.tobytes("png"))
                    method = "ocr-fallback"
                pages.append(PageText(page_number, text, method))
        return pages

    @staticmethod
    def _ocr_image(content: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - depends on deployment
            raise RuntimeError(
                "OCR requires pytesseract, Pillow, and the Tesseract binary."
            ) from exc
        image = Image.open(io.BytesIO(content)).convert("RGB")
        return pytesseract.image_to_string(image).strip()


def chunk_pages(
    document_id: str,
    source_name: str,
    pages: list[PageText],
    chunk_size: int = 900,
    overlap: int = 120,
):
    """Yield overlapping chunks without losing page-level source references."""
    from .models import SourceChunk

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    for page in pages:
        # Normalise spacing while preserving line boundaries used by field labels.
        cleaned = "\n".join(
            " ".join(line.split()) for line in page.text.splitlines() if line.strip()
        )
        if not cleaned:
            continue
        start = 0
        index = 1
        while start < len(cleaned):
            end = min(start + chunk_size, len(cleaned))
            yield SourceChunk(
                document_id=document_id,
                source_name=source_name,
                page=page.page,
                chunk_id=f"{document_id}-p{page.page}-c{index}",
                text=cleaned[start:end],
            )
            if end == len(cleaned):
                break
            start = end - overlap
            index += 1
