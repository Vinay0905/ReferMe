import pytest
from app.models.common import Subject
from app.processing.question_parser import QuestionPaperParser
from tests.fixtures.sample_question_paper import create_sample_neet_question_paper_pdf


def test_parse_sample_mock_question_paper():
    pdf_bytes = create_sample_neet_question_paper_pdf()
    parsed = QuestionPaperParser.parse(pdf_bytes)

    assert parsed.is_valid is True
    assert parsed.total_questions == 4
    assert len(parsed.questions) == 4

    # Verify Q1 structure
    q1 = parsed.questions[0]
    assert q1.question_number == 1
    assert q1.subject == Subject.PHYSICS
    assert "magnetic force" in q1.question_text
    assert len(q1.options) == 4
    assert "Both statement I and statement II are incorrect" in q1.options[0]
    assert q1.fingerprint != ""

    # Verify Q2 structure
    q2 = parsed.questions[1]
    assert q2.question_number == 2
    assert q2.subject == Subject.PHYSICS
    assert len(q2.options) == 4


def test_parse_empty_or_invalid_pdf():
    parsed_empty = QuestionPaperParser.parse(b"")
    assert parsed_empty.is_valid is False
    assert parsed_empty.warning is not None

    parsed_corrupt = QuestionPaperParser.parse(b"not a valid pdf document")
    assert parsed_corrupt.is_valid is False


def test_split_question_and_options():
    # 1. Normal standard options
    content = "A particle moves with uniform speed. (1) 10 m/s (2) 20 m/s (3) 30 m/s (4) 40 m/s"
    q_text, opts = QuestionPaperParser._split_question_and_options(content)
    assert q_text == "A particle moves with uniform speed."
    assert opts == ["10 m/s", "20 m/s", "30 m/s", "40 m/s"]

    # 2. Question containing internal numbers like (g = 10 m/s2)
    content2 = "A ball is dropped from height h (g = 10 m/s2). (1) 5 s (2) 10 s (3) 15 s (4) 20 s"
    q_text2, opts2 = QuestionPaperParser._split_question_and_options(content2)
    assert "A ball is dropped" in q_text2
    assert opts2 == ["5 s", "10 s", "15 s", "20 s"]

    # 3. Multiline options with extra whitespace
    content3 = "Find ratio of energies:\n (1) 1 : 2\n (2) 2 : 1\n (3) 3 : 1\n (4) 4 : 1"
    q_text3, opts3 = QuestionPaperParser._split_question_and_options(content3)
    assert q_text3 == "Find ratio of energies:"
    assert opts3 == ["1 : 2", "2 : 1", "3 : 1", "4 : 1"]


def test_parse_real_stored_pdf_if_available():
    import os
    path = "storage_data/test_test_5uK46Afnka7K/question_paper.pdf"
    if os.path.exists(path):
        with open(path, "rb") as f:
            pdf_bytes = f.read()
        parsed = QuestionPaperParser.parse(pdf_bytes)
        assert parsed.is_valid is True
        assert parsed.total_questions == 180
        assert len(parsed.answer_keys) == 180
        # Check that answer is attached to Q1
        assert parsed.questions[0].answer == "4"
        assert parsed.questions[45].answer == "4"
