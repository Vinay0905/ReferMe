import re
import unicodedata
from typing import Any, Dict, List, Optional
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

    # Pre-configured alias mappings: (subject, normalized_lookup_key) -> (canonical_key, canonical_display_name) or canonical_key
    DEFAULT_ALIASES: Dict[str, Dict[str, Any]] = {
        Subject.PHYSICS.value: {
            # Units, Dimensions and Measurements (resolves broken "Unit" or "Dimensions and Measurement")
            "unit": ("physics:units-dimensions-and-measurements", "Units, Dimensions and Measurements"),
            "dimensions and measurement": ("physics:units-dimensions-and-measurements", "Units, Dimensions and Measurements"),
            "units and measurements": ("physics:units-dimensions-and-measurements", "Units, Dimensions and Measurements"),
            "units dimensions and measurements": ("physics:units-dimensions-and-measurements", "Units, Dimensions and Measurements"),
            "unit dimensions and measurement": ("physics:units-dimensions-and-measurements", "Units, Dimensions and Measurements"),

            # Work, Energy and Power (resolves broken "Work" or "Energy & Power")
            "work": ("physics:work-energy-and-power", "Work, Energy and Power"),
            "energy and power": ("physics:work-energy-and-power", "Work, Energy and Power"),
            "work energy and power": ("physics:work-energy-and-power", "Work, Energy and Power"),

            # Core Physics Topics
            "shm": ("physics:simple-harmonic-motion", "Simple Harmonic Motion"),
            "em waves": ("physics:electromagnetic-waves", "Electromagnetic Waves"),
            "nlms": ("physics:laws-of-motion", "Laws of Motion"),
            "rotational motion": ("physics:rotational-motion", "Rotational Motion"),
            "ray optics": ("physics:ray-optics-and-optical-instruments", "Ray Optics & Optical Instruments"),
            "collisions and centre of mass": ("physics:collisions-and-centre-of-mass", "Collisions & Centre of Mass"),
            "basic mathematics used in physics and vectors": ("physics:basic-mathematics-used-in-physics-and-vectors", "Basic Mathematics in Physics & Vectors"),
            "kinematics and current electricity": ("physics:kinematics-and-current-electricity", "Kinematics & Current Electricity"),
            "laws of motion and friction": ("physics:laws-of-motion-and-friction", "Laws of Motion & Friction"),
            "magnetic effect of current and magnetism": ("physics:magnetic-effect-of-current-and-magnetism", "Magnetic Effects of Current & Magnetism"),

            # Experimental Skills (Unit 20 of NEET Physics)
            "vernier calipers": ("physics:exp-vernier-calipers", "Experimental Skills: Vernier Calipers"),
            "screw gauge": ("physics:exp-screw-gauge", "Experimental Skills: Screw Gauge"),
            "metre bridge": ("physics:exp-metre-bridge", "Experimental Skills: Metre Bridge"),
            "ohms law": ("physics:exp-ohms-law", "Experimental Skills: Ohm's Law"),
            "resistance of a given wire using ohms law": ("physics:exp-ohms-law", "Experimental Skills: Ohm's Law"),
            "galvanometer": ("physics:exp-galvanometer", "Experimental Skills: Galvanometer Half-Deflection"),
            "half deflection method": ("physics:exp-galvanometer", "Experimental Skills: Galvanometer Half-Deflection"),
        },
        Subject.CHEMISTRY.value: {
            "goc": ("chemistry:general-organic-chemistry", "General Organic Chemistry"),
            "p block": ("chemistry:p-block-elements", "p-Block Elements"),
            "d and f block": ("chemistry:d-and-f-block-elements", "d- and f-Block Elements"),
            "thermo": ("chemistry:thermodynamics", "Thermodynamics"),

            # Practical Chemistry
            "oxalic acid vs kmno4": ("chemistry:titration-oxalic-acid-kmno4", "Titrimetric Exercises: Oxalic Acid vs KMnO4"),
            "mohrs salt vs kmno4": ("chemistry:titration-mohrs-salt-kmno4", "Titrimetric Exercises: Mohr's Salt vs KMnO4"),
            "acids bases and the use of indicators": ("chemistry:exp-acids-bases-indicators", "Titrimetric Exercises: Acids, Bases & Indicators"),
            "enthalpy of solution of cuso4": ("chemistry:exp-enthalpy-solution-cuso4", "Thermochemistry: Enthalpy of Solution (CuSO4)"),
            "enthalpy of neutralization of strong acid and strong base": ("chemistry:exp-enthalpy-neutralization", "Thermochemistry: Enthalpy of Neutralization"),
            "preparation of lyophilic and lyophobic sols": ("chemistry:exp-colloidal-sols", "Colloidal State: Lyophilic & Lyophobic Sols"),
            "kinetic study of the reaction of iodide ions with hydrogen peroxide at room temperature": ("chemistry:exp-kinetics-iodide-h2o2", "Chemical Kinetics: Reaction of Iodide with H2O2"),
        },
        Subject.BIOLOGY.value: {
            "biomolecules": ("biology:biomolecules", "Biomolecules"),
            "genetics": ("biology:principles-of-inheritance-and-variation", "Principles of Inheritance and Variation"),
            "photosynthesis": ("biology:photosynthesis-in-higher-plants", "Photosynthesis in Higher Plants"),
            "biological classification": ("biology:biological-classification", "Biological Classification"),
            "biological classication": ("biology:biological-classification", "Biological Classification"),
            "sexual reproduction in flowering plants": ("biology:sexual-reproduction-in-flowering-plants", "Sexual Reproduction in Flowering Plants"),
            "sexual reproduction in owering plants": ("biology:sexual-reproduction-in-flowering-plants", "Sexual Reproduction in Flowering Plants"),
            "cockroach": ("biology:structural-organisation-in-animals", "Structural Organisation in Animals (Frog & Cockroach)"),
            "structural organization in animals animal tissues frog": ("biology:structural-organisation-in-animals", "Structural Organisation in Animals (Frog & Cockroach)"),
            "cell the unit of life": ("biology:cell-the-unit-of-life", "Cell: The Unit of Life"),
        }
    }

    def __init__(self, custom_aliases: Optional[Dict[str, Dict[str, Any]]] = None):
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
        # Replace backticks with apostrophes
        cleaned = cleaned.replace("`", "'")
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
        if subject_key in self.aliases:
            # 1. Exact match on lookup_slug
            alias_entry = self.aliases[subject_key].get(lookup_slug)

            # 2. If no exact match, try substring matching for multi-phrase titles
            if not alias_entry:
                for k, v in self.aliases[subject_key].items():
                    if k in lookup_slug:
                        alias_entry = v
                        break

            if alias_entry:
                if isinstance(alias_entry, (tuple, list)):
                    canonical_key, canonical_name = alias_entry[0], alias_entry[1]
                else:
                    canonical_key = alias_entry
                    canonical_name = cleaned_name

                return NormalizedTopic(
                    canonical_key=canonical_key,
                    name=canonical_name,
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
