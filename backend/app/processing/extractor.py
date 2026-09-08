import hashlib
import io
import logging
from typing import Dict, List, Optional
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
    subject_columns: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None


class PDFTextExtractor:
    """Extracts native text and page metadata from PDF bytes deterministically."""

    MIN_PDF_BYTES = 128

    @classmethod
    def sanitize_pdf_bytes(cls, content: bytes) -> bytes:
        """Unwraps raw PDF bytes if they were stored inside multipart/form-data or envelope."""
        if not content:
            return content
        pdf_start = content.find(b"%PDF-")
        if pdf_start == -1:
            return content
        eof_pos = content.rfind(b"%%EOF")
        if eof_pos != -1:
            return content[pdf_start:eof_pos + 5]
        return content[pdf_start:]

    @classmethod
    def validate_pdf_bytes(cls, content: bytes) -> bool:
        """Ensures the content contains valid PDF magic header and isn't HTML/error response."""
        if not content or len(content) < cls.MIN_PDF_BYTES:
            return False
        # Ensure it's not HTML error page
        sample = content[:300].lower()
        if b"<!doctype" in sample or b"<html" in sample or b"<xml" in sample:
            return False
        # Check PDF header (directly or within first 1KB in case of multipart boundary)
        if b"%PDF-" not in content[:1024]:
            return False
        return True

    @classmethod
    def extract(cls, content: bytes) -> ExtractionResult:
        if not cls.validate_pdf_bytes(content):
            content_hash = hashlib.sha256(content).hexdigest() if content else ""
            return ExtractionResult(
                content_hash=content_hash,
                page_count=0,
                has_extractable_text=False,
                total_characters=0,
                error="Invalid PDF bytes or HTML error response received."
            )

        content = cls.sanitize_pdf_bytes(content)
        content_hash = hashlib.sha256(content).hexdigest()

        # Attempt extraction using pdfplumber first
        try:
            import pdfplumber
            pages: List[ExtractedPage] = []
            full_text_parts: List[str] = []

            subject_columns: Dict[str, str] = {}
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

                # Column layout detection for multi-column syllabus formats (A4 landscape 3-column ALLEN syllabi)
                if pdf.pages:
                    first_page = pdf.pages[0]
                    # Must be landscape orientation (width > 700 pt)
                    if getattr(first_page, "width", 0) > 700:
                        words = first_page.extract_words()
                        if words:
                            words_sorted = sorted(words, key=lambda w: (w["top"], w["x0"]))
                            # Column boundaries: Col 1 (<300), Col 2 (300-550), Col 3 (>550)
                            col_physics = [w["text"] for w in words_sorted if w["x0"] < 300 and "allen" not in w["text"].lower()]
                            col_chemistry = [w["text"] for w in words_sorted if 300 <= w["x0"] < 550 and "allen" not in w["text"].lower()]
                            col_biology = [w["text"] for w in words_sorted if w["x0"] >= 550 and "allen" not in w["text"].lower()]

                            # Require significant content across all three columns to qualify as landscape 3-column
                            if len(col_physics) > 3 and len(col_chemistry) > 3 and len(col_biology) > 3:
                                subject_columns = {
                                    "Physics": " ".join(col_physics),
                                    "Chemistry": " ".join(col_chemistry),
                                    "Biology": " ".join(col_biology),
                                }

            total_chars = sum(p.char_count for p in pages)
            if total_chars > 20:
                return ExtractionResult(
                    content_hash=content_hash,
                    page_count=len(pages),
                    has_extractable_text=True,
                    total_characters=total_chars,
                    pages=pages,
                    raw_text="\n\n".join(full_text_parts),
                    subject_columns=subject_columns
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
