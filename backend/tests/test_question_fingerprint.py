import pytest
from app.processing.question_fingerprint import (
    compute_question_fingerprint,
    normalize_question_text,
)


def test_fingerprint_identical():
    text1 = "A particle moves with uniform acceleration along a straight line."
    text2 = "A particle moves with uniform acceleration along a straight line."
    assert compute_question_fingerprint(text1) == compute_question_fingerprint(text2)


def test_fingerprint_whitespace_tolerance():
    text1 = "A particle  moves with  uniform\nacceleration along   a straight line.  "
    text2 = "A particle moves with uniform acceleration along a straight line."
    assert compute_question_fingerprint(text1) == compute_question_fingerprint(text2)


def test_fingerprint_punctuation_and_quote_tolerance():
    text1 = "What is the ‘value’ of “momentum” - initial?"
    text2 = "What is the 'value' of \"momentum\" - initial?"
    assert compute_question_fingerprint(text1) == compute_question_fingerprint(text2)


def test_fingerprint_leading_number_stripping():
    text1 = "1) A bead is arranged to move with constant speed."
    text2 = "Q. 1 : A bead is arranged to move with constant speed."
    text3 = "45. A bead is arranged to move with constant speed."
    text4 = "A bead is arranged to move with constant speed."
    fp1 = compute_question_fingerprint(text1)
    fp2 = compute_question_fingerprint(text2)
    fp3 = compute_question_fingerprint(text3)
    fp4 = compute_question_fingerprint(text4)
    assert fp1 == fp2 == fp3 == fp4


def test_fingerprint_empty():
    assert normalize_question_text("") == ""
    assert isinstance(compute_question_fingerprint(""), str)
