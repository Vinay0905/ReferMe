import io
import logging
import os
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class QuestionCropper:
    """High-fidelity visual question snippet generator.

    Uses PyMuPDF to clip exact bounding boxes from question paper PDFs,
    and Pillow to convert them to compressed, ultra-sharp WebP assets.
    """

    DEFAULT_DPI = 180
    WEBP_QUALITY = 85

    @classmethod
    def render_crop_webp(
        cls,
        pdf_path: str,
        page_num: int,  # 1-indexed page number
        bbox: List[float],  # [x0, y0, x1, y1]
        output_path: Optional[str] = None,
        dpi: int = DEFAULT_DPI,
    ) -> Optional[bytes]:
        """Renders the bounding box from a PDF page into WebP bytes and optionally saves to disk.

        Args:
            pdf_path: Path to the question paper PDF file.
            page_num: 1-indexed page number.
            bbox: [x0, y0, x1, y1] bounding box in PDF points.
            output_path: Optional path to write the WebP file.
            dpi: Render resolution in DPI (180 DPI produces crisp retina-quality snippets).

        Returns:
            WebP encoded bytes if successful, None otherwise.
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file does not exist: {pdf_path}")
            return None

        if not bbox or len(bbox) != 4:
            logger.error(f"Invalid bounding box: {bbox}")
            return None

        try:
            doc = fitz.open(pdf_path)
            # PyMuPDF uses 0-indexed page numbers
            p_idx = page_num - 1
            if p_idx < 0 or p_idx >= len(doc):
                logger.error(f"Page {page_num} out of range for PDF {pdf_path} (total pages: {len(doc)})")
                return None

            page = doc[p_idx]
            x0, y0, x1, y1 = bbox
            # Ensure coordinates are within page dimensions and sorted
            rect = fitz.Rect(
                max(0.0, min(x0, page.rect.width)),
                max(0.0, min(y0, page.rect.height)),
                max(0.0, min(x1, page.rect.width)),
                max(0.0, min(y1, page.rect.height)),
            )

            # Check if rect has valid area
            if rect.width <= 10 or rect.height <= 10:
                logger.warning(f"Clip rect too small ({rect.width}x{rect.height}) on page {page_num}")
                rect = fitz.Rect(30.0, max(0.0, y0), page.rect.width - 30.0, min(page.rect.height, y0 + 300.0))

            # Render clip rectangle
            pix = page.get_pixmap(clip=rect, dpi=dpi)

            # Convert pixmap to WebP using Pillow
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=cls.WEBP_QUALITY, method=6)
            webp_bytes = buf.getvalue()

            # Save to disk if output_path requested
            if output_path:
                p = Path(output_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(webp_bytes)

            return webp_bytes

        except Exception as e:
            logger.error(f"Error rendering crop for {pdf_path} page {page_num}: {e}", exc_info=True)
            return None
