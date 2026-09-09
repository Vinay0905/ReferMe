import pytest
from app.models.common import Subject
from app.models.relationship import QuestionClassificationMethod
from app.processing.question_classifier import (
    CandidateTopic,
    ClassificationResult,
    QuestionClassifier,
)
from app.processing.question_parser import ExtractedQuestion


@pytest.fixture
def classifier():
    return QuestionClassifier()


@pytest.fixture
def physics_candidates():
    return [
        CandidateTopic(
            topic_id="top_units",
            canonical_key="physics:units-dimensions-and-measurements",
            name="Units, Dimensions and Measurements",
            subject=Subject.PHYSICS,
            aliases=["Unit and Measurements", "Dimensions"],
            source_text="Units, Dimensions and Measurements"
        ),
        CandidateTopic(
            topic_id="top_kinematics",
            canonical_key="physics:kinematics",
            name="Kinematics",
            subject=Subject.PHYSICS,
            aliases=["Motion in a Straight Line", "Motion in a Plane"],
            source_text="Kinematics"
        ),
        CandidateTopic(
            topic_id="top_rotational",
            canonical_key="physics:rotational-motion",
            name="Rotational Motion",
            subject=Subject.PHYSICS,
            aliases=["System of Particles and Rotational Motion"],
            source_text="Rotational Motion"
        ),
    ]


def test_structural_mapping(classifier, physics_candidates):
    q = ExtractedQuestion(
        question_number=1,
        subject_question_number=1,
        subject=Subject.PHYSICS,
        question_text="In this chapter of Units, Dimensions and Measurements, solve the following:",
        options=["1", "2", "3", "4"]
    )
    results = classifier.classify_question(q, physics_candidates)
    assert len(results) == 1
    assert results[0].canonical_key == "physics:units-dimensions-and-measurements"
    assert results[0].classification_method == QuestionClassificationMethod.STRUCTURAL
    assert results[0].confidence == 1.0


def test_fingerprint_reuse(classifier, physics_candidates):
    q = ExtractedQuestion(
        question_number=2,
        subject_question_number=2,
        subject=Subject.PHYSICS,
        question_text="A completely arbitrary text that does not match keywords.",
        options=["1", "2"],
        fingerprint="fp_hash_xyz_123"
    )
    cache = {
        "fp_hash_xyz_123": [
            ClassificationResult(
                topic_id="top_kinematics",
                canonical_key="physics:kinematics",
                subject=Subject.PHYSICS,
                classification_method=QuestionClassificationMethod.FINGERPRINT,
                confidence=1.0
            )
        ]
    }
    results = classifier.classify_question(q, physics_candidates, fingerprint_cache=cache)
    assert len(results) == 1
    assert results[0].canonical_key == "physics:kinematics"
    assert results[0].classification_method == QuestionClassificationMethod.FINGERPRINT
    assert results[0].confidence == 1.0


def test_deterministic_mapping(classifier, physics_candidates):
    q = ExtractedQuestion(
        question_number=3,
        subject_question_number=3,
        subject=Subject.PHYSICS,
        question_text="A disc is rotating about an axis. Find the moment of inertia and radius of gyration.",
        options=["mR^2", "1/2 mR^2"]
    )
    results = classifier.classify_question(q, physics_candidates)
    assert len(results) == 1
    assert results[0].canonical_key == "physics:rotational-motion"
    assert results[0].classification_method == QuestionClassificationMethod.DETERMINISTIC
    assert results[0].confidence >= 0.85


def test_unresolved_low_confidence(classifier, physics_candidates):
    # Question belongs to Optics or Biology, which is completely absent from Physics candidates
    q = ExtractedQuestion(
        question_number=4,
        subject_question_number=4,
        subject=Subject.PHYSICS,
        question_text="A ray of monochromatic light passes through a glass slab. Find refractive index.",
        options=["1.5", "1.33"]
    )
    results = classifier.classify_question(q, physics_candidates)
    assert len(results) == 0


def test_sole_candidate_topic_automatic_structural(classifier):
    single_cand = [
        CandidateTopic(
            topic_id="top_thermo",
            canonical_key="chemistry:thermodynamics",
            name="Thermodynamics",
            subject=Subject.CHEMISTRY
        )
    ]
    q = ExtractedQuestion(
        question_number=1,
        subject_question_number=1,
        subject=Subject.CHEMISTRY,
        question_text="Calculate enthalpy change for reaction A -> B.",
        options=["-10 kJ", "+10 kJ"]
    )
    results = classifier.classify_question(q, single_cand)
    assert len(results) == 1
    assert results[0].canonical_key == "chemistry:thermodynamics"
    assert results[0].classification_method == QuestionClassificationMethod.STRUCTURAL
    assert results[0].confidence == 1.0
