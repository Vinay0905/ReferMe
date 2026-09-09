import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.common import Subject
from app.models.relationship import QuestionClassificationMethod
from app.processing.question_fingerprint import normalize_question_text
from app.processing.question_parser import ExtractedQuestion

logger = logging.getLogger(__name__)


# Standard curated NCERT domain keywords for NEET topics
TOPIC_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    # Physics
    "physics:units-dimensions-and-measurements": [
        "dimension", "dimensional", "measurement", "vernier", "screw gauge",
        "error limit", "significant figures", "unit of", "least count"
    ],
    "physics:kinematics": [
        "kinematics", "motion in", "velocity", "acceleration", "displacement",
        "projectile", "speed", "trajectory", "retardation", "uniform motion"
    ],
    "physics:laws-of-motion-and-friction": [
        "force", "friction", "newton", "momentum", "impulse", "equilibrium",
        "tension", "pulley", "inclined plane", "normal reaction", "coefficient of friction"
    ],
    "physics:work-energy-and-power": [
        "kinetic energy", "potential energy", "power", "conservative force",
        "collision", "restitution", "work done", "loss of kinetic"
    ],
    "physics:rotational-motion": [
        "moment of inertia", "torque", "angular momentum", "rolling",
        "radius of gyration", "rotational", "centre of mass", "axis of rotation"
    ],
    "physics:gravitation": [
        "gravitation", "gravitational", "escape velocity", "kepler", "satellite",
        "orbital velocity", "planet", "acceleration due to gravity", "height above the surface"
    ],
    "physics:mechanical-properties-of-solids": [
        "young's modulus", "stress", "strain", "hooke's law", "bulk modulus",
        "elasticity", "wire", "elongation"
    ],
    "physics:mechanical-properties-of-fluids": [
        "viscosity", "terminal velocity", "bernoulli", "pascal", "surface tension",
        "capillary", "buoyancy", "viscous force", "lake", "glycerin", "streamline"
    ],
    "physics:thermal-properties-of-matter": [
        "calorimetry", "thermal expansion", "coefficient of expansion",
        "conduction", "convection", "radiation", "stefan", "blackbody", "apparent expansion"
    ],
    "physics:thermodynamics": [
        "isothermal", "adiabatic", "carnot", "heat engine", "internal energy",
        "first law of thermodynamics", "entropy", "efficiency of engine"
    ],
    "physics:kinetic-theory-of-gases": [
        "ideal gas", "kinetic theory", "rms speed", "degrees of freedom",
        "mean free path", "maxwell", "collision between molecules"
    ],
    "physics:oscillations": [
        "simple harmonic", "shm", "pendulum", "amplitude", "spring mass",
        "frequency", "time period", "resonance"
    ],
    "physics:waves": [
        "wave", "doppler", "sound", "resonance tube", "string", "organ pipe",
        "standing wave", "linear density"
    ],
    "physics:electrostatics": [
        "electric charge", "coulomb", "electric field", "electric potential",
        "capacitance", "capacitor", "dielectric", "gauss law"
    ],
    "physics:current-electricity": [
        "current", "resistance", "resistivity", "ohm", "kirchhoff",
        "wheatstone", "potentiometer", "meter bridge", "internal resistance", "emf"
    ],
    "physics:magnetic-effects-of-current-and-magnetism": [
        "magnetic field", "biot savart", "ampere", "solenoid", "lorentz force",
        "magnetic force", "ferromagnetic", "retentivity", "coercivity", "galvanometer"
    ],

    # Chemistry
    "chemistry:some-basic-concepts-of-chemistry": [
        "mole", "molarity", "molality", "stoichiometry", "empirical formula",
        "limiting reagent", "normality", "triad rule"
    ],
    "chemistry:structure-of-atom": [
        "bohr", "quantum number", "photoelectric", "de broglie", "heisenberg",
        "rydberg", "spectral line", "hydrogen atom", "excited to n"
    ],
    "chemistry:classification-of-elements-and-periodicity-in-properties": [
        "periodic", "ionization enthalpy", "electron gain enthalpy",
        "electronegativity", "atomic radius", "mendeleev"
    ],
    "chemistry:chemical-bonding-and-molecular-structure": [
        "hybridisation", "hybridization", "dipole moment", "bond angle",
        "vsepr", "molecular orbital", "bond order", "hydrogen bonding"
    ],
    "chemistry:thermodynamics": [
        "enthalpy", "entropy", "gibbs free energy", "internal energy change",
        "hess law", "spontaneous", "cyclic process", "work done", "delta h"
    ],
    "chemistry:equilibrium": [
        "equilibrium constant", "le chatelier", "solubility product",
        "ph of solution", "buffer", "hydrolysis", "kp", "kc", "dissociation constant"
    ],
    "chemistry:redox-reactions": [
        "oxidation number", "reducing agent", "oxidizing agent", "redox",
        "oxidation state", "balancing"
    ],

    # Biology
    "biology:the-living-world": [
        "taxonomic", "herbarium", "botanical garden", "museum", "binomial nomenclature",
        "genus", "taxonomic categories", "order", "family"
    ],
    "biology:biological-classification": [
        "monera", "protista", "fungi", "mycoplasma", "lichen", "prions",
        "virus", "viroid", "archaebacteria", "eubacteria", "chrysophytes"
    ],
    "biology:plant-kingdom": [
        "algae", "bryophytes", "pteridophytes", "gymnosperms", "angiosperms",
        "haplontic", "diplontic", "chlorophyceae", "phaeophyceae", "rhodophyceae"
    ],
    "biology:animal-kingdom": [
        "porifera", "coelenterata", "ctenophora", "platyhelminthes", "aschelminthes",
        "annelida", "arthropoda", "mollusca", "echinodermata", "chordata", "non-chordate"
    ],
    "biology:morphology-of-flowering-plants": [
        "root", "stem", "leaf", "inflorescence", "flower", "fruit", "seed",
        "placentation", "aestivation", "marginal", "axile", "parietal", "basal"
    ],
    "biology:anatomy-of-flowering-plants": [
        "meristematic", "xylem", "phloem", "stomata", "vascular bundle",
        "cambium", "cortex", "secondary growth", "collenchyma", "parenchyma"
    ],
    "biology:cell-the-unit-of-life": [
        "mitochondria", "chloroplast", "golgi", "endoplasmic reticulum", "ribosome",
        "nucleus", "plasma membrane", "lysosome", "mesosome", "eukaryotic", "prokaryotic"
    ],
    "biology:biomolecules": [
        "amino acid", "protein", "carbohydrate", "lipid", "nucleic acid",
        "enzyme", "activation energy", "co-factor", "prosthetic group", "peptide bond"
    ],
    "biology:cell-cycle-and-cell-division": [
        "mitosis", "meiosis", "prophase", "metaphase", "anaphase", "telophase",
        "cytokinesis", "crossing over", "chiasmata", "interphase", "bivalent", "tetrad"
    ],
    "biology:photosynthesis-in-higher-plants": [
        "chlorophyll", "photosynthesis", "light reaction", "dark reaction",
        "calvin cycle", "c4 pathway", "c3 pathway", "photorespiration", "rubisco", "thylakoid"
    ],
    "biology:respiration-in-plants": [
        "glycolysis", "fermentation", "krebs cycle", "electron transport",
        "respiratory quotient", "oxidative phosphorylation", "atp synthase"
    ],
    "biology:plant-growth-and-development": [
        "auxin", "gibberellin", "cytokinin", "ethylene", "abscisic acid",
        "photoperiodism", "vernalization", "seed dormancy", "apical dominance", "phytohormone"
    ],
    "biology:locomotion-and-movement": [
        "skeletal muscle", "actin", "myosin", "sarcomere", "pectoral", "pelvic",
        "girdle", "coxal bone", "joint", "tetany", "myasthenia gravis", "osteoporosis"
    ],
    "biology:chemical-coordination-and-integration": [
        "pituitary", "thyroid", "adrenal", "pars distalis", "vasopressin",
        "oxytocin", "growth hormone", "prolactin", "calcitonin", "hormone"
    ],
}


@dataclass
class CandidateTopic:
    topic_id: str
    canonical_key: str
    name: str
    subject: Subject
    aliases: List[str] = field(default_factory=list)
    source_text: Optional[str] = None


@dataclass
class ClassificationResult:
    topic_id: str
    canonical_key: str
    subject: Subject
    classification_method: QuestionClassificationMethod
    confidence: float
    match_reason: str = ""


class AIClassifierInterface:
    """Pluggable, isolated AI classification interface."""

    async def classify(
        self, question: ExtractedQuestion, candidate_topics: List[CandidateTopic]
    ) -> Optional[List[ClassificationResult]]:
        return None


class NullAIClassifier(AIClassifierInterface):
    """Default no-op AI classifier ensuring zero external dependency."""

    pass


class QuestionClassifier:
    """Layered question classifier strictly scoped to a test's syllabus topics.

    Layers:
    1. Structural Mapping (confidence 1.0)
    2. Fingerprint Reuse (confidence 1.0)
    3. Deterministic Rules / Aliases / Domain Keywords (confidence 0.85 - 0.95)
    4. Lightweight TF-IDF Cosine Similarity (confidence >= 0.25)
    5. AI Fallback (optional, bypassed by default)
    """

    TFIDF_THRESHOLD = 0.20

    def __init__(self, ai_classifier: Optional[AIClassifierInterface] = None):
        self.ai_classifier = ai_classifier or NullAIClassifier()

    def classify_question(
        self,
        question: ExtractedQuestion,
        candidate_topics: List[CandidateTopic],
        fingerprint_cache: Optional[Dict[str, List[ClassificationResult]]] = None,
    ) -> List[ClassificationResult]:
        """Classifies an extracted question against syllabus-scoped candidate topics."""
        # Filter candidate topics to match the question's subject
        candidates = [t for t in candidate_topics if t.subject == question.subject]
        if not candidates:
            return []

        # If only 1 candidate topic exists for this subject in the test (e.g. single-chapter Unit test)
        if len(candidates) == 1:
            only = candidates[0]
            return [
                ClassificationResult(
                    topic_id=only.topic_id,
                    canonical_key=only.canonical_key,
                    subject=only.subject,
                    classification_method=QuestionClassificationMethod.STRUCTURAL,
                    confidence=1.0,
                    match_reason=f"Sole candidate topic in test syllabus for {question.subject.value}",
                )
            ]

        # ---------------------------------------------------------------------
        # Layer 1: Structural Mapping
        # ---------------------------------------------------------------------
        structural_match = self._try_structural_mapping(question, candidates)
        if structural_match:
            return [structural_match]

        # ---------------------------------------------------------------------
        # Layer 2: Fingerprint Reuse
        # ---------------------------------------------------------------------
        if fingerprint_cache and question.fingerprint:
            cached = fingerprint_cache.get(question.fingerprint)
            if cached:
                # Ensure the cached topic is among the current test's candidates
                valid_cached = [
                    ClassificationResult(
                        topic_id=c.topic_id,
                        canonical_key=c.canonical_key,
                        subject=c.subject,
                        classification_method=QuestionClassificationMethod.FINGERPRINT,
                        confidence=1.0,
                        match_reason=f"Reused from identical question fingerprint {question.fingerprint[:12]}",
                    )
                    for c in cached
                    if any(cand.topic_id == c.topic_id for cand in candidates)
                ]
                if valid_cached:
                    return valid_cached

        # ---------------------------------------------------------------------
        # Layer 3: Deterministic Rules & Domain Keywords
        # ---------------------------------------------------------------------
        deterministic_matches = self._try_deterministic_rules(question, candidates)
        if deterministic_matches:
            return deterministic_matches

        # ---------------------------------------------------------------------
        # Layer 4: Lightweight TF-IDF Cosine Similarity
        # ---------------------------------------------------------------------
        tfidf_matches = self._try_tfidf_similarity(question, candidates)
        if tfidf_matches:
            return tfidf_matches

        # If none matched above threshold, return empty (marked UNRESOLVED)
        return []

    def _try_structural_mapping(
        self, question: ExtractedQuestion, candidates: List[CandidateTopic]
    ) -> Optional[ClassificationResult]:
        """Checks for exact chapter, experiment, or unit phrases in the question text."""
        q_lower = normalize_question_text(question.question_text)

        for cand in candidates:
            c_name = normalize_question_text(cand.name)
            if len(c_name) > 8 and c_name in q_lower:
                return ClassificationResult(
                    topic_id=cand.topic_id,
                    canonical_key=cand.canonical_key,
                    subject=cand.subject,
                    classification_method=QuestionClassificationMethod.STRUCTURAL,
                    confidence=1.0,
                    match_reason=f"Exact candidate name '{cand.name}' found in question text",
                )
            if cand.source_text:
                s_text = normalize_question_text(cand.source_text)
                if len(s_text) > 8 and s_text in q_lower:
                    return ClassificationResult(
                        topic_id=cand.topic_id,
                        canonical_key=cand.canonical_key,
                        subject=cand.subject,
                        classification_method=QuestionClassificationMethod.STRUCTURAL,
                        confidence=1.0,
                        match_reason=f"Exact syllabus text '{cand.source_text}' found in question text",
                    )
        return None

    def _try_deterministic_rules(
        self, question: ExtractedQuestion, candidates: List[CandidateTopic]
    ) -> List[ClassificationResult]:
        """Matches domain-specific terminology, key concepts, and aliases against candidate topics."""
        q_lower = normalize_question_text(question.question_text)
        q_tokens = set(re.findall(r"\b\w{4,}\b", q_lower))

        best_score = 0
        best_cand: Optional[CandidateTopic] = None
        best_term = ""

        for cand in candidates:
            # Collect terms from name, aliases, source_text, slug
            terms = [cand.name] + cand.aliases
            slug_terms = cand.canonical_key.split(":")[-1].replace("-", " ")
            terms.append(slug_terms)
            if cand.source_text:
                terms.append(cand.source_text)

            # Also include domain keywords if registered for this canonical key
            domain_kws = TOPIC_DOMAIN_KEYWORDS.get(cand.canonical_key, [])
            terms.extend(domain_kws)

            score = 0
            matched_terms = []
            for term in terms:
                cleaned_term = normalize_question_text(term)
                # Check multi-word phrase exact match in question text
                if " " in cleaned_term and cleaned_term in q_lower:
                    score += 20
                    matched_terms.append(cleaned_term)
                else:
                    # Token root matching
                    term_words = [w for w in cleaned_term.split() if len(w) >= 4]
                    for tw in term_words:
                        # Direct match
                        if tw in q_tokens or re.search(rf"\b{re.escape(tw)}\b", q_lower):
                            score += 6
                            matched_terms.append(tw)
                        else:
                            # Prefix root matching (e.g. dimension vs dimensional)
                            if len(tw) >= 5:
                                for qw in q_tokens:
                                    if len(qw) >= 5 and (tw[:5] == qw[:5]):
                                        score += 5
                                        matched_terms.append(f"{tw}~{qw}")
                                        break

            if score > best_score:
                best_score = score
                best_cand = cand
                best_term = ", ".join(matched_terms[:3])

        # Require a threshold score of at least 10
        if best_cand and best_score >= 10:
            confidence = min(0.95, 0.82 + (best_score / 100.0))
            return [
                ClassificationResult(
                    topic_id=best_cand.topic_id,
                    canonical_key=best_cand.canonical_key,
                    subject=best_cand.subject,
                    classification_method=QuestionClassificationMethod.DETERMINISTIC,
                    confidence=round(confidence, 2),
                    match_reason=f"Deterministic match ({best_term}) score={best_score}",
                )
            ]

        return []

    def _try_tfidf_similarity(
        self, question: ExtractedQuestion, candidates: List[CandidateTopic]
    ) -> List[ClassificationResult]:
        """Calculates TF-IDF cosine similarity between question and candidate topic representations."""
        if not candidates:
            return []

        candidate_docs = []
        for cand in candidates:
            doc_parts = [cand.name] + cand.aliases
            if cand.source_text:
                doc_parts.append(cand.source_text)
            doc_parts.append(cand.canonical_key.split(":")[-1].replace("-", " "))
            domain_kws = TOPIC_DOMAIN_KEYWORDS.get(cand.canonical_key, [])
            doc_parts.extend(domain_kws)
            candidate_docs.append(" ".join(doc_parts))

        corpus = candidate_docs + [question.question_text]

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)
            question_vec = tfidf_matrix[-1]
            candidate_vecs = tfidf_matrix[:-1]

            similarities = cosine_similarity(question_vec, candidate_vecs).flatten()
            best_idx = int(similarities.argmax())
            best_sim = float(similarities[best_idx])

            if best_sim >= self.TFIDF_THRESHOLD:
                cand = candidates[best_idx]
                confidence = round(min(0.90, best_sim), 2)
                return [
                    ClassificationResult(
                        topic_id=cand.topic_id,
                        canonical_key=cand.canonical_key,
                        subject=cand.subject,
                        classification_method=QuestionClassificationMethod.TFIDF,
                        confidence=confidence,
                        match_reason=f"TF-IDF cosine similarity={best_sim:.3f}",
                    )
                ]
        except Exception as e:
            logger.debug(f"TF-IDF similarity calculation failed: {e}")

        return []
