"""
nlp/preprocessor.py — Text cleaning, normalization, and section detection
"""
import re
from dataclasses import dataclass, field
from typing import Optional
import nltk
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Download NLTK data on first use
_NLTK_DOWNLOADED = False

def _ensure_nltk():
    global _NLTK_DOWNLOADED
    if not _NLTK_DOWNLOADED:
        for pkg in ["punkt", "stopwords", "wordnet", "omw-1.4"]:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass
        _NLTK_DOWNLOADED = True


# ── Section patterns ────────────────────────────────────────────
SECTION_PATTERNS = {
    "summary":       r"(summary|objective|profile|about me|professional summary)",
    "experience":    r"(experience|employment|work history|career|positions? held)",
    "education":     r"(education|academic|qualification|degree|university|college)",
    "skills":        r"(skills?|technical skills?|competenc|proficienc|expertise)",
    "projects":      r"(projects?|portfolio|open.?source|side projects?)",
    "certifications":r"(certifications?|licenses?|credentials?|courses?|training)",
    "achievements":  r"(achievements?|awards?|honors?|accomplishments?)",
    "publications":  r"(publications?|research|papers?|articles?)",
    "languages":     r"(languages?|spoken|linguistic)",
}


@dataclass
class ParsedDocument:
    """Structure holding raw and cleaned text plus detected sections."""
    raw_text: str
    clean_text: str
    sections: dict[str, str] = field(default_factory=dict)
    tokens: list[str] = field(default_factory=list)


class TextPreprocessor:
    """
    Handles all text cleaning and section segmentation.
    spaCy is used for lemmatization when available; falls back to NLTK.
    """

    def __init__(self):
        self._nlp = None   # lazy-load spaCy to keep import fast

    def _load_spacy(self):
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
                logger.info("spaCy model loaded")
            except Exception as exc:
                logger.warning("spaCy not available, using NLTK fallback", error=str(exc))
                self._nlp = False
        return self._nlp

    # ── Public API ─────────────────────────────────────────────
    def process(self, text: str) -> ParsedDocument:
        """Full pipeline: clean → section split → tokenise/lemmatise."""
        clean = self.clean(text)
        sections = self.detect_sections(text)
        tokens = self.tokenize_and_lemmatize(clean)
        return ParsedDocument(
            raw_text=text,
            clean_text=clean,
            sections=sections,
            tokens=tokens,
        )

    def clean(self, text: str) -> str:
        """Normalize whitespace, lowercase, strip special chars."""
        text = text.lower()
        text = re.sub(r"https?://\S+", " ", text)           # remove URLs
        text = re.sub(r"\S+@\S+", " ", text)                # remove emails
        text = re.sub(r"\+?\d[\d\s\-\(\)]{7,}\d", " ", text)  # remove phone numbers
        text = re.sub(r"[^a-z0-9\s\-\+\#\.]", " ", text)    # keep alphanumeric + tech chars
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def tokenize_and_lemmatize(self, text: str) -> list[str]:
        """Return lemmatized, stop-word-free tokens."""
        nlp = self._load_spacy()
        if nlp:
            doc = nlp(text[:1_000_000])          # spaCy max length guard
            return [
                token.lemma_
                for token in doc
                if not token.is_stop and not token.is_punct and len(token.text) > 1
            ]
        # NLTK fallback
        _ensure_nltk()
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        stop_words = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()
        tokens = word_tokenize(text)
        return [
            lemmatizer.lemmatize(t)
            for t in tokens
            if t.isalpha() and t not in stop_words and len(t) > 1
        ]

    def detect_sections(self, text: str) -> dict[str, str]:
        """
        Split raw resume text into named sections.
        Returns a dict mapping section name → section content.
        """
        lines = text.split("\n")
        sections: dict[str, list[str]] = {"other": []}
        current = "other"

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            detected = self._match_section_header(stripped)
            if detected:
                current = detected
                sections.setdefault(current, [])
            else:
                sections.setdefault(current, []).append(stripped)

        return {k: "\n".join(v) for k, v in sections.items() if v}

    @staticmethod
    def _match_section_header(line: str) -> Optional[str]:
        """Return section name if the line looks like a section header, else None."""
        if len(line) > 60:       # headers are rarely long
            return None
        lower = line.lower().strip(": \t-–—")
        for section, pattern in SECTION_PATTERNS.items():
            if re.fullmatch(pattern, lower):
                return section
            if re.search(pattern, lower) and len(lower) < 30:
                return section
        return None


# Module-level singleton
preprocessor = TextPreprocessor()
