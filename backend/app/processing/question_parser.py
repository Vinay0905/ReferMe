import io
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pdfplumber
from app.models.common import Subject
from app.processing.question_fingerprint import (
    compute_question_fingerprint,
    normalize_question_text,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedQuestion:
    question_number: int  # Global test question index (1..180)
    subject_question_number: int  # Subject question index (1..45 or 1..90)
    subject: Subject
    question_text: str
    options: List[str]
    answer: Optional[str] = None
    source_page: int = 1
    bounding_box: Optional[List[float]] = None  # [x0, y0, x1, y1] on source_page
    normalized_question_text: str = ""
    fingerprint: str = ""


@dataclass
class ParsedQuestionPaper:
    is_valid: bool
    questions: List[ExtractedQuestion] = field(default_factory=list)
    answer_keys: Dict[int, str] = field(default_factory=dict)
    total_questions: int = 0
    parser_version: str = "v1"
    warning: Optional[str] = None


class QuestionPaperParser:
    """Deterministic, rule-based parser for ALLEN NEET question papers.

    Extracts questions, multiline options, subjects, answer keys, and page numbers.
    """

    VERSION = "v1"

    # Regex for start of question: e.g. "1) ...", "  45) ..."
    Q_START_REGEX = re.compile(r"^\s*(\d+)\)\s*(.*)$")

    # Header / footer lines to ignore
    HEADER_IGNORE_PATTERNS = [
        re.compile(r"^\d{2}-\d{2}-\d{4}$"),  # Dates like 26-04-2026
        re.compile(r"^\d{4}[A-Z]{3}\d+$"),   # Roll / test identifiers like 0999DMD363101250017
        re.compile(r"^ALLEN CAREER INSTITUTE", re.I),
        re.compile(r"^TEST CODE:", re.I),
        re.compile(r"^MD$", re.I),
        re.compile(r"^--+$"),
    ]

    @classmethod
    def parse(cls, pdf_bytes: bytes) -> ParsedQuestionPaper:
        """Parses an ALLEN NEET question paper PDF into structured ExtractedQuestion objects."""
        if not pdf_bytes:
            return ParsedQuestionPaper(is_valid=False, warning="Empty PDF bytes.")

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                if not pdf.pages:
                    return ParsedQuestionPaper(is_valid=False, warning="PDF contains no pages.")

                # 1. Parse Answer Keys first if present
                answer_keys = cls._extract_answer_keys(pdf)

                # 2. Extract raw question blocks across pages up to the answer key section
                raw_questions, bboxes_by_q = cls._extract_raw_question_blocks_and_bboxes(pdf)

                # 3. Refine questions: split question text from options, attach answers and fingerprints
                questions: List[ExtractedQuestion] = []
                subject_counters: Dict[Subject, int] = {
                    Subject.PHYSICS: 0,
                    Subject.CHEMISTRY: 0,
                    Subject.BIOLOGY: 0,
                }
                global_q_counter = 0

                for raw_q in raw_questions:
                    subject = raw_q["subject"]
                    subject_counters[subject] = subject_counters.get(subject, 0) + 1
                    global_q_counter += 1

                    full_content = " ".join(raw_q["lines"]).strip()
                    q_text, options = cls._split_question_and_options(full_content)

                    # Determine global question number
                    q_num = raw_q["num"]
                    # If numbering restarted in Chemistry/Biology (e.g. 1..45 instead of 46..90):
                    # In NEET: Physics is 1..45, Chemistry is 46..90, Biology is 91..180
                    global_num = global_q_counter
                    if subject == Subject.PHYSICS:
                        subject_q_num = q_num
                    elif subject == Subject.CHEMISTRY:
                        subject_q_num = q_num if q_num <= 45 else (q_num - 45)
                    else:  # BIOLOGY
                        subject_q_num = q_num if q_num <= 90 else (q_num - 90)

                    # Look up answer in answer keys
                    # Check global_num first, then raw q_num
                    answer = answer_keys.get(global_num) or answer_keys.get(q_num)

                    norm_text = normalize_question_text(q_text)
                    fingerprint = compute_question_fingerprint(q_text)
                    bbox = bboxes_by_q.get((raw_q["page"], q_num))

                    questions.append(
                        ExtractedQuestion(
                            question_number=global_num,
                            subject_question_number=subject_q_num,
                            subject=subject,
                            question_text=q_text,
                            options=options,
                            answer=answer,
                            source_page=raw_q["page"],
                            bounding_box=bbox,
                            normalized_question_text=norm_text,
                            fingerprint=fingerprint,
                        )
                    )

                return ParsedQuestionPaper(
                    is_valid=len(questions) > 0,
                    questions=questions,
                    answer_keys=answer_keys,
                    total_questions=len(questions),
                    parser_version=cls.VERSION,
                )

        except Exception as err:
            logger.error(f"Error parsing question paper PDF: {err}", exc_info=True)
            return ParsedQuestionPaper(is_valid=False, warning=str(err))

    @classmethod
    def _extract_answer_keys(cls, pdf: pdfplumber.PDF) -> Dict[int, str]:
        """Scans pages for the ANSWER KEYS section and maps question numbers to answers."""
        ak_dict: Dict[int, str] = {}
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "ANSWER KEY" in text.upper() or "ANSWER KEYS" in text.upper():
                lines = text.split("\n")
                current_qs: List[int] = []
                for line in lines:
                    line_s = line.strip()
                    if re.match(r"^Q\.\s*", line_s, re.I) or re.match(r"^Q:\s*", line_s, re.I):
                        nums = [int(x) for x in re.findall(r"\d+", line_s)]
                        current_qs = nums
                    elif re.match(r"^A\.\s*", line_s, re.I) or re.match(r"^A:\s*", line_s, re.I):
                        # Extract answer tokens after A. or A:
                        prefix_match = re.match(r"^A[\.:]\s*(.*)$", line_s, re.I)
                        if prefix_match:
                            answers = prefix_match.group(1).split()
                            if current_qs and len(current_qs) == len(answers):
                                for q_num, ans in zip(current_qs, answers):
                                    ak_dict[q_num] = ans.strip()
                                current_qs = []
        return ak_dict

    @classmethod
    def _extract_raw_question_blocks_and_bboxes(
        cls, pdf: pdfplumber.PDF
    ) -> (List[Dict], Dict[tuple, List[float]]):
        """Extracts question line blocks and calculates high-precision bounding boxes per question."""
        raw_questions: List[Dict] = []
        bboxes_by_q: Dict[tuple, List[float]] = {}
        current_subject = Subject.PHYSICS
        current_q: Optional[Dict] = None

        q_word_re = re.compile(r"^(\d{1,3})\)$")

        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            # Once we reach ANSWER KEYS or SOLUTIONS, question paper questions have concluded
            upper_text = text.upper()
            if "ANSWER KEY" in upper_text or "ANSWER KEYS" in upper_text or "HINTS & SOLUTIONS" in upper_text or "\nSOLUTIONS\n" in upper_text:
                break

            page_num = page_idx + 1
            lines = text.split("\n")
            for line in lines:
                line_s = line.strip()
                if not line_s:
                    continue

                # Check subject headings
                upper_line = line_s.upper()
                if upper_line in ["PHYSICS", "CHEMISTRY", "BIOLOGY", "BOTANY", "ZOOLOGY"]:
                    if upper_line in ["BOTANY", "ZOOLOGY"]:
                        current_subject = Subject.BIOLOGY
                    elif upper_line == "CHEMISTRY":
                        current_subject = Subject.CHEMISTRY
                    elif upper_line == "PHYSICS":
                        current_subject = Subject.PHYSICS
                    elif upper_line == "BIOLOGY":
                        current_subject = Subject.BIOLOGY
                    continue

                # Ignore known header noise
                if any(p.search(line_s) for p in cls.HEADER_IGNORE_PATTERNS):
                    continue

                # Match question start
                m = cls.Q_START_REGEX.match(line_s)
                if m:
                    if current_q:
                        raw_questions.append(current_q)
                    current_q = {
                        "num": int(m.group(1)),
                        "subject": current_subject,
                        "page": page_num,
                        "lines": [m.group(2)] if m.group(2) else [],
                    }
                else:
                    if current_q:
                        current_q["lines"].append(line_s)

            # Compute bounding boxes for questions on this page
            try:
                words = page.extract_words()
                q_markers = []
                for w in words:
                    if w["x0"] < 55 and q_word_re.match(w["text"]):
                        num = int(q_word_re.match(w["text"]).group(1))
                        q_markers.append((num, float(w["top"])))

                page_w = float(page.width)
                page_h = float(page.height)
                for i, (num, top) in enumerate(q_markers):
                    y0 = max(0.0, top - 6.0)
                    if i + 1 < len(q_markers):
                        y1 = q_markers[i + 1][1] - 4.0
                    else:
                        y1 = min(page_h - 15.0, top + 350.0)
                    bboxes_by_q[(page_num, num)] = [
                        round(30.0, 1),
                        round(y0, 1),
                        round(page_w - 30.0, 1),
                        round(y1, 1),
                    ]
            except Exception as e:
                logger.warning(f"Error computing bounding boxes on page {page_num}: {e}")

        if current_q:
            raw_questions.append(current_q)

        return raw_questions, bboxes_by_q

    @classmethod
    def _split_question_and_options(cls, full_content: str) -> (str, List[str]):
        """Splits full content into question text and clean options (1)-(4)."""
        # Find all matches for (1), (2), (3), (4)
        matches = list(re.finditer(r"(?:^|\s)\(([1-4])\)", full_content))
        if not matches:
            # Fallback: check for (a), (b), (c), (d)
            matches = list(re.finditer(r"(?:^|\s)\(([a-d])\)", full_content, re.I))
            if not matches:
                clean_q = re.sub(r"\s+", " ", full_content).strip()
                return clean_q, []

        # Find the best starting point for the 4 options:
        # We look for the last occurrence where option 1 is followed by 2, 3, 4
        ones = [i for i, m in enumerate(matches) if m.group(1).lower() in ("1", "a")]
        best_start = 0
        for one_idx in reversed(ones):
            sub = [m.group(1).lower() for m in matches[one_idx:]]
            if ("2" in sub or "b" in sub) and ("3" in sub or "c" in sub) and ("4" in sub or "d" in sub):
                best_start = one_idx
                break

        selected_matches = matches[best_start:]
        q_text_end = selected_matches[0].start()
        q_text = full_content[:q_text_end].strip()
        q_text = re.sub(r"\s+", " ", q_text)

        options: List[str] = []
        for i in range(len(selected_matches)):
            m = selected_matches[i]
            s = m.end()
            e = selected_matches[i + 1].start() if i + 1 < len(selected_matches) else len(full_content)
            opt_str = full_content[s:e].strip()
            opt_str = re.sub(r"\s+", " ", opt_str)
            options.append(opt_str)

        return q_text, options
