import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.common import Subject
from app.processing.extractor import ExtractionResult


class ParsedTopic(BaseModel):
    subject: Subject
    raw_topic: str
    section_name: Optional[str] = None  # e.g., Chapter or Unit name if available
    page_number: int = 1
    confidence: float = 1.0


class ParsedSyllabus(BaseModel):
    parser_version: str = "v1"
    test_title: Optional[str] = None
    target_exam: Optional[str] = None
    date_str: Optional[str] = None
    topics: List[ParsedTopic] = Field(default_factory=list)
    raw_sections: Dict[str, List[str]] = Field(default_factory=dict)
    is_valid: bool = False
    warning: Optional[str] = None


class SyllabusParser:
    """Deterministic structural parser for NEET syllabi."""

    VERSION = "v1"

    # Regex patterns for subject headers
    SUBJECT_PATTERNS = {
        Subject.PHYSICS: re.compile(r"^\s*(?:SUBJECT\s*[:\-])?\s*PHYSICS\b", re.IGNORECASE),
        Subject.CHEMISTRY: re.compile(r"^\s*(?:SUBJECT\s*[:\-])?\s*CHEMISTRY\b", re.IGNORECASE),
        Subject.BIOLOGY: re.compile(r"^\s*(?:SUBJECT\s*[:\-])?\s*(?:BIOLOGY|BOTANY|ZOOLOGY)\b", re.IGNORECASE),
    }

    # Common boilerplate lines to ignore
    BOILERPLATE_PATTERNS = [
        re.compile(r"^page\s+\d+\s+of\s+\d+", re.IGNORECASE),
        re.compile(r"^allen\s+career\s+institute", re.IGNORECASE),
        re.compile(r"^corporate\s+office\b", re.IGNORECASE),
        re.compile(r"^test\s+syllabus\b", re.IGNORECASE),
        re.compile(r"^schedule\s+&\s+syllabus\b", re.IGNORECASE),
        re.compile(r"^\*+\s*confidential\s*\*+", re.IGNORECASE),
        re.compile(r"^time\s*:\s*\d+", re.IGNORECASE),
        re.compile(r"^max(?:imum)?\s+marks\s*:\s*\d+", re.IGNORECASE),
    ]

    @classmethod
    def parse(cls, extraction: ExtractionResult) -> ParsedSyllabus:
        if not extraction.has_extractable_text:
            return ParsedSyllabus(
                parser_version=cls.VERSION,
                is_valid=False,
                warning="Extraction result contains no extractable text."
            )

        test_title = None
        target_exam = None
        date_str = None
        parsed_topics: List[ParsedTopic] = []
        raw_sections: Dict[str, List[str]] = {s.value: [] for s in Subject}

        current_subject: Optional[Subject] = None

        # Check if 3-column layout was detected (A4 landscape ALLEN syllabus format)
        if extraction.subject_columns and any(len(txt.strip()) > 3 for txt in extraction.subject_columns.values()):
            for subj_name, col_text in extraction.subject_columns.items():
                try:
                    subject = Subject(subj_name)
                except ValueError:
                    continue
                if col_text.strip():
                    raw_sections[subject.value].append(col_text)
                    topics = cls._extract_topics_from_text(col_text, subject, page_number=1)
                    parsed_topics.extend(topics)
        else:
            # Traditional line-by-line header detection
            for page in extraction.pages:
                lines = page.text.splitlines()

                for line in lines:
                    clean_line = line.strip()
                    if not clean_line:
                        continue

                    # Detect metadata if at top of syllabus
                    if not target_exam and re.search(r"NEET\s*\(?UG\)?", clean_line, re.IGNORECASE):
                        target_exam = "NEET (UG)"

                    if not test_title:
                        match_title = re.search(r"(MINOR\s+TEST\s*\([^)]+\)|MAJOR\s+TEST\s*\([^)]+\)|OPEN\s+TEST\s*\([^)]+\)|ALL\s+INDIA\s+OPEN\s+TEST\s*\([^)]+\)|TEST\s*-\s*\d+)", clean_line, re.IGNORECASE)
                        if match_title:
                            test_title = match_title.group(1).upper()

                    if not date_str:
                        match_date = re.search(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(?:20\d\d)?)\b", clean_line, re.IGNORECASE)
                        if match_date:
                            date_str = match_date.group(1)

                    # Skip header/footer boilerplate
                    if any(bp.match(clean_line) for bp in cls.BOILERPLATE_PATTERNS):
                        continue

                    # Check if this line introduces a new Subject header
                    matched_subj = cls._detect_subject_header(clean_line)
                    if matched_subj:
                        current_subject = matched_subj
                        remaining = cls._strip_subject_prefix(clean_line, matched_subj)
                        if remaining:
                            raw_sections[current_subject.value].append(remaining)
                            topics = cls._extract_topics_from_text(remaining, current_subject, page.page_number)
                            parsed_topics.extend(topics)
                        continue

                    # If inside a known subject section, process the line
                    if current_subject:
                        raw_sections[current_subject.value].append(clean_line)
                        topics = cls._extract_topics_from_text(clean_line, current_subject, page.page_number)
                        parsed_topics.extend(topics)

        # Deduplicate identical raw topics within the same subject & page
        unique_topics: List[ParsedTopic] = []
        seen_keys = set()
        for t in parsed_topics:
            key = (t.subject.value, t.raw_topic.strip().lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_topics.append(t)

        is_valid = len(unique_topics) > 0

        return ParsedSyllabus(
            parser_version=cls.VERSION,
            test_title=test_title,
            target_exam=target_exam,
            date_str=date_str,
            topics=unique_topics,
            raw_sections=raw_sections,
            is_valid=is_valid,
            warning=None if is_valid else "No valid subject sections or topics could be parsed."
        )

    @classmethod
    def _detect_subject_header(cls, line: str) -> Optional[Subject]:
        for subject, pattern in cls.SUBJECT_PATTERNS.items():
            if pattern.search(line):
                return subject
        return None

    @classmethod
    def _strip_subject_prefix(cls, line: str, subject: Subject) -> str:
        pattern = cls.SUBJECT_PATTERNS[subject]
        stripped = pattern.sub("", line).strip()
        # Strip leading punctuation like colon or hyphen
        return re.sub(r"^[:\-\s]+", "", stripped).strip()

    @classmethod
    def _clean_raw_text(cls, text: str) -> str:
        """Repairs dropped font ligatures, typographic apostrophes, and protects compound chapters."""
        if not text:
            return ""
        # 1. Ligatures and OCR artifacts
        text = re.sub(r"\bclassi\s*cation\b", "Classification", text, flags=re.IGNORECASE)
        text = re.sub(r"\bclassication\b", "Classification", text, flags=re.IGNORECASE)
        text = re.sub(r"(?<=\s)owering\b", "flowering", text, flags=re.IGNORECASE)
        text = re.sub(r"\bowering\b", "flowering", text, flags=re.IGNORECASE)
        text = re.sub(r"\bde\s*ection\b", "deflection", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdeection\b", "deflection", text, flags=re.IGNORECASE)
        text = re.sub(r"\boxalicacid\b", "Oxalic Acid", text, flags=re.IGNORECASE)

        # 2. Quotes & Punctuation
        text = text.replace("`", "'").replace("’", "'").replace("‘", "'")

        # 3. Compound chapter protection before comma splitting
        # In NEET syllabus, these chapters contain commas. We protect them so comma-splitting does not shatter them.
        text = re.sub(r"\bUnits?,\s*Dimensions?\s*and\s*Measurements?\b", "Units and Measurements", text, flags=re.IGNORECASE)
        text = re.sub(r"\bUnit,\s*Dimensions and Measurement\b", "Units and Measurements", text, flags=re.IGNORECASE)
        text = re.sub(r"\bWork,\s*Energy\s*(&|and)\s*Power\b", "Work Energy and Power", text, flags=re.IGNORECASE)
        text = re.sub(r"\bAcids,\s*bases\s*and\s*the\s*use\s*of\s*indicators\b", "Acids Bases and the Use of Indicators", text, flags=re.IGNORECASE)

        return text

    @classmethod
    def _extract_topics_from_text(cls, text: str, subject: Subject, page_number: int) -> List[ParsedTopic]:
        """Parses chapter prefixes and splits delimited topic items."""
        results: List[ParsedTopic] = []

        # Pre-clean text for ligatures and protected compound chapters
        text = cls._clean_raw_text(text)

        # Split on bullet points first so multi-topic paragraphs are grouped cleanly
        chunks = [c.strip() for c in re.split(r"[•·]+", text) if c.strip()]
        if not chunks:
            chunks = [text.strip()]

        for chunk in chunks:
            # Clean null bytes and leading punctuation
            chunk = chunk.replace("\x00", "").strip()
            if not chunk or "allen" in chunk.lower():
                continue

            # Check for chapter/unit prefix, e.g. "Chapter Name: Topic 1, Topic 2"
            section_name = None
            topic_body = chunk

            if ":" in chunk:
                parts = chunk.split(":", 1)
                candidate_section = parts[0].strip()
                if len(candidate_section) < 60 and not any(p in candidate_section for p in [",", ";"]):
                    candidate_clean = re.sub(r"^(?:\d+[\.\)]|\-|\*|•)\s*", "", candidate_section).strip()
                    # Strip any subject labels if present in section header
                    candidate_clean = re.sub(r"^(?:PHYSICS|CHEMISTRY|BIOLOGY|BOTANY|ZOOLOGY)\s*[:\-]\s*", "", candidate_clean, flags=re.IGNORECASE).strip()
                    if candidate_clean:
                        section_name = candidate_clean
                    topic_body = parts[1].strip()

            # Split on commas, semicolons, pipe symbols, or double hyphens
            raw_items = re.split(r"[;,|]+|\s+--\s+", topic_body)

            for item in raw_items:
                clean_item = item.strip()
                # Remove leading numbering like "1. ", "a) ", "(i) ", "- "
                clean_item = re.sub(r"^(?:(?:\d+|[a-zA-Z]|\([a-zA-Z0-9]+\))[\.\)]|\-|\*)\s*", "", clean_item).strip()
                # Remove any accidental leading subject labels (e.g. "CHEMISTRY: ", "BIOLOGY: ")
                clean_item = re.sub(r"^(?:PHYSICS|CHEMISTRY|BIOLOGY|BOTANY|ZOOLOGY)\s*[:\-]\s*", "", clean_item, flags=re.IGNORECASE).strip()
                clean_item = clean_item.replace("\x00", "").strip()

                # Clean trailing periods or commas
                clean_item = clean_item.rstrip(".,;").strip()

                item_sec = section_name
                # Detect sub-section headers embedded in item
                if re.search(r"\bexperimental\s+skills\b\s*:", clean_item, re.IGNORECASE):
                    item_sec = "Experimental Skills"
                    clean_item = re.sub(r"^experimental\s+skills\s*:\s*", "", clean_item, flags=re.IGNORECASE).strip()
                elif re.search(r"\bprinciples\s+related\s+to\s+practical\s+chemistry\b\s*:", clean_item, re.IGNORECASE):
                    item_sec = "Practical Chemistry"
                    clean_item = re.sub(r"^principles\s+related\s+to\s+practical\s+chemistry\s*:\s*(?:the\s+chemistry\s+involved\s+in\s+the\s+titrimetric\s+exercises\s*[-–]\s*)?", "", clean_item, flags=re.IGNORECASE).strip()
                elif clean_item.lower().startswith("chemical principles involved in the following experiments:"):
                    item_sec = "Practical Chemistry"
                    clean_item = re.sub(r"^chemical\s+principles\s+involved\s+in\s+the\s+following\s+experiments:\s*\d*[\.\)]?\s*", "", clean_item, flags=re.IGNORECASE).strip()

                # Remove numeric prefixes after extraction
                clean_item = re.sub(r"^\d+[\.\)]\s*", "", clean_item).strip()

                if len(clean_item) < 3 or "allen" in clean_item.lower():
                    continue

                if re.match(r"^(?:section\s+[ab]|total\s+marks|part\s+\d+|optional)\b", clean_item, re.IGNORECASE):
                    continue

                results.append(ParsedTopic(
                    subject=subject,
                    raw_topic=clean_item,
                    section_name=item_sec,
                    page_number=page_number,
                    confidence=1.0
                ))

        return results
