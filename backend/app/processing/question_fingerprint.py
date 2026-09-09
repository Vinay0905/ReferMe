import hashlib
import re


def normalize_question_text(text: str) -> str:
    """Deterministically normalizes question text for hashing and fingerprinting.

    Strips leading question numbers, standardizes quotes/whitespace, and lowercases.
    """
    if not text:
        return ""

    normalized = text.lower().strip()
    # Strip leading question indicators (e.g. "1)", "1.", "Q.1", "Q. 1 :", "1 -")
    normalized = re.sub(r"^(?:q(?:uestion)?\.?\s*)?\d+\s*[\)\.:\-]\s*", "", normalized)


    # Standardize typographic quotes and special characters
    normalized = re.sub(r"[`'‘’‛′]", "'", normalized)
    normalized = re.sub(r'["“”‟″]', '"', normalized)
    normalized = re.sub(r"[–—−]", "-", normalized)

    # Collapse multiple whitespaces and trim
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def compute_question_fingerprint(text: str) -> str:
    """Computes a stable SHA-256 fingerprint from the normalized question text."""
    normalized = normalize_question_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
