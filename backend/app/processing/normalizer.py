import re
import unicodedata
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.models.common import Subject
from app.models.relationship import NormalizationMethod
from app.processing.parser import ParsedTopic


class NormalizedTopic(BaseModel):
    canonical_key: str
    name: str  # Clean display name
    subject: Subject
    raw_source_text: str
    section_name: Optional[str] = None
    method: NormalizationMethod = NormalizationMethod.DETERMINISTIC
    confidence: float = 1.0


class TopicNormalizer:
    """Normalizes raw syllabus topic strings into canonical keys and display names."""

    # Pre-configured alias mappings: (subject, normalized_lookup_key) -> (canonical_key, canonical_display_name)
    DEFAULT_ALIASES: Dict[str, Dict[str, str]] = {
        Subject.PHYSICS.value: {
            "shm": "physics:simple-harmonic-motion",
            "em waves": "physics:electromagnetic-waves",
            "nlms": "physics:laws-of-motion",
            "rotational motion": "physics:rotational-motion",
            "ray optics": "physics:ray-optics-and-optical-instruments",
        },
        Subject.CHEMISTRY.value: {
            "goc": "chemistry:general-organic-chemistry",
            "p block": "chemistry:p-block-elements",
            "d and f block": "chemistry:d-and-f-block-elements",
            "thermo": "chemistry:thermodynamics",
        },
        Subject.BIOLOGY.value: {
            "biomolecules": "biology:biomolecules",
            "genetics": "biology:principles-of-inheritance-and-variation",
            "photosynthesis": "biology:photosynthesis-in-higher-plants",
        }
    }

    def __init__(self, custom_aliases: Optional[Dict[str, Dict[str, str]]] = None):
        self.aliases = self.DEFAULT_ALIASES.copy()
        if custom_aliases:
            for subj, mappings in custom_aliases.items():
                if subj in self.aliases:
                    self.aliases[subj].update(mappings)
                else:
                    self.aliases[subj] = mappings

    @classmethod
    def slugify(cls, text: str) -> str:
        """Converts text to an alphanumeric hyphenated slug."""
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        # Replace '&' with 'and'
        text = re.sub(r"&", "and", text)
        # Replace non-alphanumeric chars with hyphen
        text = re.sub(r"[^\w\s-]", "", text).strip().lower()
        # Replace whitespace or multiple hyphens with a single hyphen
        return re.sub(r"[-\s]+", "-", text).strip("-")

    @classmethod
    def clean_display_name(cls, raw: str) -> str:
        """Cleans raw topic text into a neat, human-readable display name."""
        # Strip outer quotes and punctuation
        cleaned = raw.strip().strip("'\".,;:()")
        # Strip leading numbering like "1. ", "a) ", "(i) ", "- ", "• "
        cleaned = re.sub(r"^(?:(?:\d+|[a-zA-Z]|\([a-zA-Z0-9]+\))[\.\)]|\-|\*|•)\s*", "", cleaned).strip()
        # Normalize internal whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)
        # Ensure title-like capitalization if all lowercase or all uppercase
        if cleaned.islower() or cleaned.isupper():
            cleaned = cleaned.title()
        return cleaned

    def normalize(self, parsed: ParsedTopic) -> NormalizedTopic:
        raw_text = parsed.raw_topic.strip()
        cleaned_name = self.clean_display_name(raw_text)
        slug = self.slugify(cleaned_name)

        subject_key = parsed.subject.value
        lookup_slug = slug.replace("-", " ")

        # Check if subject has alias matching
        if subject_key in self.aliases and lookup_slug in self.aliases[subject_key]:
            canonical_key = self.aliases[subject_key][lookup_slug]
            return NormalizedTopic(
                canonical_key=canonical_key,
                name=cleaned_name,
                subject=parsed.subject,
                raw_source_text=raw_text,
                section_name=parsed.section_name,
                method=NormalizationMethod.ALIAS,
                confidence=1.0
            )

        # Dynamic canonical key generation
        canonical_key = f"{parsed.subject.value.lower()}:{slug}"

        return NormalizedTopic(
            canonical_key=canonical_key,
            name=cleaned_name,
            subject=parsed.subject,
            raw_source_text=raw_text,
            section_name=parsed.section_name,
            method=NormalizationMethod.DETERMINISTIC,
            confidence=1.0
        )

    def normalize_all(self, parsed_topics: List[ParsedTopic]) -> List[NormalizedTopic]:
        results: List[NormalizedTopic] = []
        seen_canonical = set()

        for pt in parsed_topics:
            norm = self.normalize(pt)
            # Avoid duplicate canonical keys from the same test syllabus
            if (norm.subject.value, norm.canonical_key) not in seen_canonical:
                seen_canonical.add((norm.subject.value, norm.canonical_key))
                results.append(norm)

        return results
