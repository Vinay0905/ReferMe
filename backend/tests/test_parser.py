import pytest
from app.models.common import Subject
from app.models.relationship import NormalizationMethod
from app.processing.extractor import ExtractionResult, ExtractedPage, PDFTextExtractor
from app.processing.normalizer import TopicNormalizer
from app.processing.parser import SyllabusParser, ParsedTopic
from tests.fixtures.sample_syllabus import (
    SAMPLE_RAW_SYLLABUS_TEXT,
    create_sample_neet_syllabus_pdf,
)


def test_pdf_validation():
    # Invalid: empty or too short
    assert PDFTextExtractor.validate_pdf_bytes(b"") is False
    assert PDFTextExtractor.validate_pdf_bytes(b"%PDF-short") is False

    # Invalid: HTML error page
    html_error = b"<!DOCTYPE html><html><body>403 Forbidden</body></html>" + b" " * 100
    assert PDFTextExtractor.validate_pdf_bytes(html_error) is False

    # Valid PDF header
    valid_header = b"%PDF-1.4" + b"0" * 150
    assert PDFTextExtractor.validate_pdf_bytes(valid_header) is True


def test_pdf_extraction_from_bytes():
    pdf_bytes = create_sample_neet_syllabus_pdf()
    result = PDFTextExtractor.extract(pdf_bytes)

    assert result.has_extractable_text is True
    assert result.page_count >= 1
    assert result.total_characters > 50
    assert "PHYSICS" in result.raw_text.upper()
    assert result.content_hash != ""


def test_syllabus_parser_with_sample_text():
    # Simulate extraction result with realistic syllabus text
    extraction = ExtractionResult(
        content_hash="mock_hash_123",
        page_count=1,
        has_extractable_text=True,
        total_characters=len(SAMPLE_RAW_SYLLABUS_TEXT),
        pages=[ExtractedPage(page_number=1, text=SAMPLE_RAW_SYLLABUS_TEXT, char_count=len(SAMPLE_RAW_SYLLABUS_TEXT))],
        raw_text=SAMPLE_RAW_SYLLABUS_TEXT,
    )

    parsed = SyllabusParser.parse(extraction)

    assert parsed.is_valid is True
    assert parsed.target_exam == "NEET (UG)"
    assert parsed.test_title == "MINOR TEST (DLP)"
    assert parsed.date_str == "13 Sep 2026"
    assert len(parsed.topics) > 10

    # Verify subject breakdown
    physics_topics = [t for t in parsed.topics if t.subject == Subject.PHYSICS]
    chemistry_topics = [t for t in parsed.topics if t.subject == Subject.CHEMISTRY]
    biology_topics = [t for t in parsed.topics if t.subject == Subject.BIOLOGY]

    assert len(physics_topics) > 0
    assert len(chemistry_topics) > 0
    assert len(biology_topics) > 0

    # Verify specific topics and section names extracted
    current_elec_topics = [t for t in physics_topics if t.section_name == "Current Electricity"]
    assert len(current_elec_topics) >= 4
    raw_texts = [t.raw_topic for t in current_elec_topics]
    assert any("Ohm's Law" in r for r in raw_texts)
    assert any("Kirchhoff's Laws" in r for r in raw_texts)


def test_topic_normalizer_slugify_and_clean():
    # Test slugification
    assert TopicNormalizer.slugify("Electric Power") == "electric-power"
    assert TopicNormalizer.slugify("Ohm's Law") == "ohms-law"
    assert TopicNormalizer.slugify("Cell Cycle & Cell Division") == "cell-cycle-and-cell-division"
    assert TopicNormalizer.slugify("d- and f-Block Elements") == "d-and-f-block-elements"

    # Test clean display name
    assert TopicNormalizer.clean_display_name("  electric current... ") == "Electric Current"
    assert TopicNormalizer.clean_display_name("1. OHM'S LAW") == "Ohm'S Law"


def test_topic_normalizer_dynamic_and_alias():
    normalizer = TopicNormalizer()

    # 1. Deterministic normalization
    pt1 = ParsedTopic(
        subject=Subject.PHYSICS,
        raw_topic="Electric Current",
        section_name="Current Electricity"
    )
    norm1 = normalizer.normalize(pt1)
    assert norm1.canonical_key == "physics:electric-current"
    assert norm1.name == "Electric Current"
    assert norm1.method == NormalizationMethod.DETERMINISTIC

    # 2. Alias mapping normalization
    pt2 = ParsedTopic(
        subject=Subject.PHYSICS,
        raw_topic="SHM",
        section_name="Oscillations"
    )
    norm2 = normalizer.normalize(pt2)
    assert norm2.canonical_key == "physics:simple-harmonic-motion"
    assert norm2.method == NormalizationMethod.ALIAS

    # 3. Deduplication in normalize_all
    pt3_dup = ParsedTopic(
        subject=Subject.PHYSICS,
        raw_topic="Electric Current",
        section_name="Current Electricity"
    )
    all_norms = normalizer.normalize_all([pt1, pt2, pt3_dup])
    assert len(all_norms) == 2  # pt3_dup deduplicated


def test_syllabus_parser_empty_or_malformed():
    empty_extraction = ExtractionResult(
        content_hash="empty_hash",
        page_count=0,
        has_extractable_text=False,
        total_characters=0,
        raw_text=""
    )
    parsed = SyllabusParser.parse(empty_extraction)
    assert parsed.is_valid is False
    assert parsed.warning is not None

    unrelated_extraction = ExtractionResult(
        content_hash="random_hash",
        page_count=1,
        has_extractable_text=True,
        total_characters=100,
        pages=[ExtractedPage(page_number=1, text="Just a random document with no syllabus headers", char_count=45)],
        raw_text="Just a random document with no syllabus headers"
    )
    parsed_unrelated = SyllabusParser.parse(unrelated_extraction)
    assert parsed_unrelated.is_valid is False
    assert len(parsed_unrelated.topics) == 0
