import hashlib
import io
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    char_count: int


class ExtractionResult(BaseModel):
    content_hash: str
    page_count: int
    has_extractable_text: bool
    total_characters: int
    pages: List[ExtractedPage] = Field(default_factory=list)
    raw_text: str = ""
    error: Optional[str] = None


class PDFTextExtractor:
    """Extracts native text and page metadata from PDF bytes deterministically."""

    MIN_PDF_BYTES = 128

    @classmethod
    def validate_pdf_bytes(cls, content: bytes) -> bool:
        """Ensures the content has valid PDF magic header and isn't HTML/error response."""
        if not content or len(content) < cls.MIN_PDF_BYTES:
            return False
        # Check PDF header
        if not content.startswith(b"%PDF-"):
            return False
        # Ensure it's not HTML error page
        sample = content[:200].lower()
        if b"<!doctype" in sample or b"<html" in sample or b"<xml" in sample:
            return False
        return True

    @classmethod
    def extract(cls, content: bytes) -> ExtractionResult:
        content_hash = hashlib.sha256(content).hexdigest()

        if not cls.validate_pdf_bytes(content):
            return ExtractionResult(
                content_hash=content_hash,
                page_count=0,
                has_extractable_text=False,
                total_characters=0,
                error="Invalid PDF bytes or HTML error response received."
            )

        # Attempt extraction using pdfplumber first
        try:
            import pdfplumber
            pages: List[ExtractedPage] = []
            full_text_parts: List[str] = []

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(layout=True) or ""
                    clean_text = text.strip()
                    pages.append(ExtractedPage(
                        page_number=idx,
                        text=clean_text,
                        char_count=len(clean_text)
                    ))
                    if clean_text:
                        full_text_parts.append(clean_text)

            total_chars = sum(p.char_count for p in pages)
            if total_chars > 20:
                return ExtractionResult(
                    content_hash=content_hash,
                    page_count=len(pages),
                    has_extractable_text=True,
                    total_characters=total_chars,
                    pages=pages,
                    raw_text="\n\n".join(full_text_parts)
                )
            logger.info("pdfplumber extracted insufficient text; trying pypdf fallback.")
        except Exception as plumber_err:
            logger.warning(f"pdfplumber extraction failed: {plumber_err}, attempting pypdf fallback.")

        # Fallback: pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = []
            full_text_parts = []

            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                clean_text = text.strip()
                pages.append(ExtractedPage(
                    page_number=idx,
                    text=clean_text,
                    char_count=len(clean_text)
                ))
                if clean_text:
                    full_text_parts.append(clean_text)

            total_chars = sum(p.char_count for p in pages)
            return ExtractionResult(
                content_hash=content_hash,
                page_count=len(pages),
                has_extractable_text=total_chars > 20,
                total_characters=total_chars,
                pages=pages,
                raw_text="\n\n".join(full_text_parts)
            )
        except Exception as pypdf_err:
            logger.error(f"Both pdfplumber and pypdf extraction failed: {pypdf_err}")
            return ExtractionResult(
                content_hash=content_hash,
                page_count=0,
                has_extractable_text=False,
                total_characters=0,
                error=f"PDF extraction error: {str(pypdf_err)}"
            )
