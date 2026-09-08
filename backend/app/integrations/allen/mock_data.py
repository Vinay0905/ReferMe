from typing import Any, Dict, List
from tests.fixtures.sample_syllabus import create_sample_neet_syllabus_pdf
from tests.fixtures.sample_question_paper import create_sample_neet_question_paper_pdf

MOCK_ALLEN_TEST_CARDS: List[Dict[str, Any]] = [
    {
        "test_id": "test_101",
        "title": "MINOR TEST - 1 (DLP)",
        "status": "FINAL_RESULT_GENERATED",
        "label": "PAST TEST",
        "labels": [
            {"text": "13 Sep"},
            {"text": "180 Min"},
            {"text": "Offline"}
        ],
        "category": "DLP",
        "link_cta": {
            "label": "View Syllabus",
            "action": {
                "type": "FETCH",
                "data": {
                    "uri": "/api/v1/tests/test_101/syllabus",
                    "method": "POST"
                }
            }
        }
    },
    {
        "test_id": "test_102",
        "title": "MINOR TEST - 2 (DLP)",
        "status": "FINAL_RESULT_GENERATED",
        "label": "PAST TEST",
        "labels": [
            {"text": "27 Sep"},
            {"text": "180 Min"},
            {"text": "Offline"}
        ],
        "category": "DLP",
        "link_cta": {
            "label": "View Syllabus",
            "action": {
                "type": "FETCH",
                "data": {
                    "uri": "/api/v1/tests/test_102/syllabus",
                    "method": "POST"
                }
            }
        }
    },
    {
        "test_id": "test_103",
        "title": "MAJOR TEST - 1 (ALL INDIA OPEN)",
        "status": "UPCOMING",
        "label": "UPCOMING TEST",
        "labels": [
            {"text": "15 Oct"},
            {"text": "200 Min"},
            {"text": "Online"}
        ],
        "category": "MAJOR",
        "link_cta": {
            "label": "View Syllabus",
            "action": {
                "type": "FETCH",
                "data": {
                    "uri": "/api/v1/tests/test_103/syllabus",
                    "method": "POST"
                }
            }
        }
    }
]


def get_mock_syllabus_pdf_bytes(test_id: str) -> bytes:
    """Returns realistic mock PDF bytes for testing."""
    return create_sample_neet_syllabus_pdf()


def get_mock_question_paper_pdf_bytes(test_id: str) -> bytes:
    """Returns realistic mock question paper PDF bytes for testing."""
    return create_sample_neet_question_paper_pdf()
