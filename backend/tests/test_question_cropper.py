import pytest
import os
from pathlib import Path
from app.processing.question_cropper import QuestionCropper


def test_question_cropper_valid_crop():
    base_dir = Path(__file__).resolve().parent.parent
    sample_pdf = None
    for p in (base_dir / "storage_data").glob("test_*/question_paper.pdf"):
        sample_pdf = str(p)
        break

    if not sample_pdf:
        pytest.skip("No question paper PDFs available for visual crop test.")

    # Render a test crop for page 1
    bbox = [30.0, 100.0, 565.0, 300.0]
    out_file = str(base_dir / "storage_data" / "pytest_sample_crop.webp")

    webp_data = QuestionCropper.render_crop_webp(
        pdf_path=sample_pdf,
        page_num=1,
        bbox=bbox,
        output_path=out_file,
    )

    assert webp_data is not None
    assert len(webp_data) > 0
    # Verify WebP RIFF header
    assert webp_data[:4] == b"RIFF"
    assert webp_data[8:12] == b"WEBP"
    assert os.path.exists(out_file)

    # Clean up test output
    if os.path.exists(out_file):
        os.remove(out_file)


def test_question_cropper_invalid_inputs():
    # Non-existent PDF
    res = QuestionCropper.render_crop_webp(
        pdf_path="non_existent.pdf",
        page_num=1,
        bbox=[30.0, 50.0, 500.0, 200.0],
    )
    assert res is None

    # Invalid bounding box
    res = QuestionCropper.render_crop_webp(
        pdf_path="non_existent.pdf",
        page_num=1,
        bbox=[30.0],
    )
    assert res is None
