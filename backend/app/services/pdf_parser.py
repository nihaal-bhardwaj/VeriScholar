"""PDF parsing service built on PyMuPDF.

Extracts raw text, page-wise text, DOI candidates, title, authors, abstract,
and references sections from an in-memory PDF byte buffer. The parsing is
intentionally heuristic and modular, so sections can be extended without
touching the route layer.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import fitz  # PyMuPDF

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
DOI_TRAILING_PUNCTUATION = ".,;:!?)]}"

ABSTRACT_HEADINGS = ("abstract", "summary")
ABSTRACT_STOP_HEADINGS = (
    "accepted",
    "citation",
    "funding",
    "index terms",
    "introduction",
    "keywords",
    "received",
    "1. introduction",
    "1 introduction",
    "i. introduction",
    "i introduction",
)
ABSTRACT_STOP_COLON_PATTERN = re.compile(
    r"^\s*(?:accepted|citation|funding|index terms|keywords|received)\s*:",
    re.IGNORECASE,
)

REFERENCES_HEADINGS = ("references", "bibliography", "references and notes")
KEYWORDS_HEADINGS = ("keywords", "index terms")

KEYWORDS_STOP_HEADINGS = (
    "1. introduction",
    "1 introduction",
    "2. introduction",
    "2 introduction",
    "i. introduction",
    "i introduction",
    "introduction",
    "1. method",
    "1 method",
    "2. method",
    "2 method",
    "method",
    "abstract",
    "references",
)

# Pattern to detect numbered/lettered section headings (e.g. "1. Introduction", "A. Background", "I. Introduction")
NUMBERED_SECTION_HEADING = re.compile(
    r"^\s*(?:\d{1,2}|[A-Z]|[IVXLCDM]+)\.?\s+[A-Z]",
    re.IGNORECASE,
)

LIGATURE_MAP = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

JOURNAL_HEADER_PATTERNS = [
    re.compile(r"^\s*PROCEEDINGS OF THE IEEE\b.*$", re.IGNORECASE),
    re.compile(r"^\s*IEEE TRANSACTIONS ON\b.*$", re.IGNORECASE),
    re.compile(r"^\s*IEEE JOURNAL\b.*$", re.IGNORECASE),
    re.compile(r"^\s*INVITED PAPER\s*$", re.IGNORECASE),
    re.compile(r"^\s*REGULAR PAPER\s*$", re.IGNORECASE),
    re.compile(r"^\s*REVIEW PAPER\s*$", re.IGNORECASE),
    re.compile(r"^\s*MANUSCRIPT RECEIVED\b.*$", re.IGNORECASE),
    re.compile(r"^\s*IEEE LOG NUMBER\b.*$", re.IGNORECASE),
    re.compile(r"^\s*AUTHORIZED LICENSED USE\b.*$", re.IGNORECASE),
    re.compile(r"^\s*\d{4}-\d{4}/\d{2}.*IEEE.*$", re.IGNORECASE),
]

STANDALONE_PAGE_NUMBER = re.compile(r"^\s*\d{1,4}\s*$")

IEEE_MEMBERSHIP_PATTERN = re.compile(
    r"\b(?:FELLOW|SENIOR MEMBER|MEMBER|STUDENT MEMBER|LIFE FELLOW|LIFE MEMBER|"
    r"LIFE SENIOR MEMBER|ASSOCIATE MEMBER)\s*,?\s*IEEE\b",
    re.IGNORECASE,
)

AFFILIATION_KEYWORDS = re.compile(
    r"\b(?:academy|association|clinic|college|consortium|council|corporation|"
    r"department|division|faculty|foundation|group|hospital|incorporated|"
    r"institute|laborator(?:y|ies)|medical|polytechnic|school|society|unit|"
    r"university|centre|center)\b",
    re.IGNORECASE,
)

GRANT_AND_METADATA_PATTERN = re.compile(
    r"\b(?:manuscript received|this work was supported|the authors are with|"
    r"supported in part by|ieee log number|authorized licensed use|reprint requests)\b",
    re.IGNORECASE,
)


class PDFParseError(Exception):
    """Raised when a PDF cannot be opened or read."""


class PDFPasswordProtectedError(PDFParseError):
    """Raised when a PDF requires a password."""


class PDFCorruptError(PDFParseError):
    """Raised when a PDF is damaged and cannot be parsed."""


@dataclass
class ExtractedPaper:
    """Parsed content of a single PDF document."""

    filename: str
    file_size_bytes: int
    page_count: int
    pages: list[dict] = field(default_factory=list)
    raw_text: str = ""
    doi_candidates: list[str] = field(default_factory=list)
    best_doi: str | None = None
    abstract: str | None = None
    abstract_status: str = "uncertain"
    abstract_confidence: float | None = None
    title: str | None = None
    title_confidence: float | None = None
    title_source: str | None = None
    authors: list[str] = field(default_factory=list)
    author_confidence: float | None = None
    author_source: str | None = None
    keywords: list[str] = field(default_factory=list)
    references_text: str | None = None
    references: list[dict] = field(default_factory=list)
    reference_validation: dict | None = None
    extraction_quality: dict | None = None
    warnings: list[str] = field(default_factory=list)


def _clean_doi(candidate: str) -> str:
    """Strip trailing punctuation from a raw DOI candidate."""
    return candidate.rstrip(DOI_TRAILING_PUNCTUATION)


def extract_doi_candidates(text: str) -> list[str]:
    """Return deduplicated, case-normalized DOI candidates from text."""
    candidates: list[str] = []
    seen: set[str] = set()
    for match in DOI_PATTERN.findall(text):
        cleaned = _clean_doi(match)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            candidates.append(cleaned)
    return candidates


def normalize_pdf_text(raw_text: str) -> str:
    """Multi-pass text normalization for challenging academic PDFs."""
    if not raw_text:
        return ""

    # 1. Normalize Unicode (NFKC)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Resolve ligatures
    for lig, replacement in LIGATURE_MAP.items():
        text = text.replace(lig, replacement)

    # 3. Repair line-break hyphenation (e.g. "distribu-\nted" -> "distributed")
    text = re.sub(r"([a-z]{2,})-\s*(?:\r?\n|\n)\s*([a-z]{2,})", r"\1\2", text)
    text = re.sub(r"([A-Z][a-z]+)-\s*(?:\r?\n|\n)\s*([a-z]{2,})", r"\1\2", text)

    return text


def _lines_with_heading(lines: list[str], headings: tuple[str, ...]) -> list[tuple[int, str, str]]:
    """Return (index, matched heading, heading line) for lines matching a heading."""
    matches: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        stripped = line.strip().rstrip(":").lower()
        if stripped in headings:
            matches.append((index, stripped, line))
    return matches


def _section_between(
    lines: list[str],
    start_index: int,
    stop_headings: tuple[str, ...],
    stop_colon_pattern: re.Pattern[str] | None = None,
) -> str:
    """Join lines from start_index until a stop heading is found."""
    collected: list[str] = []
    for line in lines[start_index + 1 :]:
        normalized = line.strip().rstrip(":").strip().lower()
        if normalized in stop_headings:
            break
        if stop_colon_pattern is not None and stop_colon_pattern.match(line):
            break
        collected.append(line.strip())
    while collected and not collected[-1]:
        collected.pop()
    return "\n".join(collected).strip() or None


ABSTRACT_EM_DASH_PATTERN = re.compile(
    r"^\s*(?:abstract|summary)\b\s*[-—–:]\s*(.*)$",
    re.IGNORECASE,
)
SPACED_ABSTRACT_PATTERN = re.compile(
    r"^\s*A\s*B\s*S\s*T\s*R\s*A\s*C\s*T\b\s*[-—–:]?\s*(.*)$",
    re.IGNORECASE,
)

PAPER_LABELS = re.compile(
    r"^\s*(?:invited\s+paper|review\s+paper|tutorial\s+paper|original\s+article|research\s+article|special\s+issue|brief\s+report)\b",
    re.IGNORECASE,
)
DECORATIVE_CHARS = re.compile(r"^[~_\-+=*#\s\u2014\u2013]+$")


def _clean_and_validate_abstract(
    text: str, authors: list[str] | None = None, min_words: int = 20
) -> tuple[str | None, str, float]:
    """Purify abstract text and validate against front-matter contamination.

    Returns (cleaned_text, status, confidence).
    """
    if not text:
        return None, "uncertain", 0.0

    # 1. Line-by-line filtering of front-matter / grant / metadata contamination
    cleaned_lines = []
    for line in text.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        if DECORATIVE_CHARS.match(line_s):
            continue
        if PAPER_LABELS.match(line_s):
            continue
        if _is_journal_header(line_s):
            continue
        if GRANT_AND_METADATA_PATTERN.search(line_s):
            continue
        if IEEE_MEMBERSHIP_PATTERN.search(line_s):
            continue
        if AFFILIATION_KEYWORDS.search(line_s):
            continue
        if authors and any(a.lower() in line_s.lower() for a in authors if len(a.strip()) > 3):
            continue
        cleaned_lines.append(line_s)

    cleaned = " ".join(cleaned_lines).strip()

    # 2. Strip leading decorative characters or repeated symbols
    cleaned = re.sub(r"^[~_\-+=*#\s\u2014\u2013]+", "", cleaned).strip()

    # 3. Strip leading paper labels (e.g. 'Invited Paper')
    cleaned = PAPER_LABELS.sub("", cleaned).strip()

    # 4. Strip leading author strings / IEEE membership if prepended
    cleaned = re.sub(
        r"^[A-Z\s.,&'-]+(?:FELLOW|MEMBER|SENIOR MEMBER|STUDENT MEMBER|LIFE FELLOW),\s*IEEE[A-Z\s.,&'-]*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = PAPER_LABELS.sub("", cleaned).strip()
    cleaned = re.sub(r"^[~_\-+=*#\s\u2014\u2013]+", "", cleaned).strip()

    # 5. Check for residual contamination
    has_contamination = False
    if IEEE_MEMBERSHIP_PATTERN.search(cleaned):
        has_contamination = True
    if PAPER_LABELS.search(cleaned):
        has_contamination = True
    if GRANT_AND_METADATA_PATTERN.search(cleaned):
        has_contamination = True
    if authors:
        for author in authors:
            if author.strip() and len(author.strip()) > 3 and author.lower() in cleaned.lower():
                has_contamination = True
                break

    words = cleaned.split()
    if len(words) < min_words:
        return cleaned or None, "uncertain", 0.40

    if has_contamination:
        return cleaned, "uncertain", 0.50

    return cleaned, "found", 0.95


def _detect_abstract(lines: list[str]) -> str | None:
    """Find the abstract section between Abstract/Summary and a stop heading."""
    abstract, _, _ = _detect_abstract_detailed(lines)
    return abstract


def _detect_abstract_detailed(
    lines: list[str], authors: list[str] | None = None
) -> tuple[str | None, str, float]:
    """Detect abstract with exact status ('found', 'absent', 'uncertain') and confidence."""
    # 1. Check for inline em-dash or spaced heading
    for index, line in enumerate(lines):
        em_match = ABSTRACT_EM_DASH_PATTERN.match(line) or SPACED_ABSTRACT_PATTERN.match(line)
        if em_match:
            inline_text = em_match.group(1).strip()
            collected: list[str] = []
            if inline_text:
                collected.append(inline_text)
            for following_line in lines[index + 1 :]:
                norm = following_line.strip().rstrip(":").strip().lower()
                if (
                    norm in ABSTRACT_STOP_HEADINGS
                    or any(
                        norm.startswith(h)
                        for h in (
                            "index terms",
                            "keywords",
                            "1. introduction",
                            "1 introduction",
                            "i. introduction",
                            "introduction",
                        )
                    )
                ):
                    break
                if ABSTRACT_STOP_COLON_PATTERN.match(following_line):
                    break
                if NUMBERED_SECTION_HEADING.match(following_line) and "introduction" in norm:
                    break
                collected.append(following_line.strip())
            while collected and not collected[-1]:
                collected.pop()
            raw_text = "\n".join(collected).strip()
            return _clean_and_validate_abstract(raw_text, authors, min_words=8)

    # 2. Check standard bare heading
    for index, _, _ in _lines_with_heading(lines, ABSTRACT_HEADINGS):
        section = _section_between(
            lines, index, ABSTRACT_STOP_HEADINGS, ABSTRACT_STOP_COLON_PATTERN
        )
        if section and len(section.split()) >= 10:
            return _clean_and_validate_abstract(section, authors, min_words=8)

    # 3. Fallback: unlabelled abstract between front-matter and Introduction
    intro_index = None
    for index, line in enumerate(lines[:60]):
        norm = line.strip().rstrip(":").strip().lower()
        if (
            norm in ("introduction", "1. introduction", "1 introduction", "i. introduction")
            or (NUMBERED_SECTION_HEADING.match(line) and "introduction" in norm)
        ):
            intro_index = index
            break

    if intro_index is not None and intro_index >= 3:
        # Search forward after author block for actual abstract prose start
        prose_start = None
        for i in range(2, intro_index):
            l = lines[i]
            if DECORATIVE_CHARS.match(l):
                continue
            if IEEE_MEMBERSHIP_PATTERN.search(l):
                continue
            if AFFILIATION_KEYWORDS.search(l):
                continue
            if FRONT_MATTER_METADATA_LABEL.match(l):
                continue
            if PAPER_LABELS.match(l):
                continue
            if _is_journal_header(l):
                continue
            if GRANT_AND_METADATA_PATTERN.search(l):
                continue
            if authors and any(a.lower() in l.lower() for a in authors if len(a.strip()) > 3):
                continue
            words = l.split()
            if len(words) >= 3 and words[0][0].isupper():
                prose_start = i
                break

        if prose_start is not None and prose_start < intro_index:
            raw_text = "\n".join(l.strip() for l in lines[prose_start:intro_index] if l.strip())
            return _clean_and_validate_abstract(raw_text, authors)

    # 4. Check if document genuinely has no abstract (absent)
    if intro_index is not None and intro_index <= 3:
        return None, "absent", 0.80

    return None, "uncertain", 0.0


def _detect_references(lines: list[str]) -> str | None:
    """Find the references section starting at the References heading."""
    for index, _, _ in _lines_with_heading(lines, REFERENCES_HEADINGS):
        section = _section_between(lines, index, ())
        if section:
            return section
    return None


def _detect_keywords(lines: list[str]) -> list[str]:
    """Extract keywords from the Keywords or Index Terms section."""
    keywords_heading_pattern = re.compile(
        r"^\s*(?:keywords|index terms)\s*[-—–:]", re.IGNORECASE
    )

    for index, line in enumerate(lines):
        if not keywords_heading_pattern.match(line):
            continue

        colon_pos = line.find(":")
        dash_pos = max(line.find("—"), line.find("-"), line.find("–"))
        sep_pos = colon_pos if colon_pos != -1 else dash_pos

        inline_content = ""
        if sep_pos != -1:
            inline_content = line[sep_pos + 1 :].strip()

        section_lines: list[str] = []
        if inline_content:
            section_lines.append(inline_content)

        for following_line in lines[index + 1 :]:
            normalized = following_line.strip().rstrip(":").strip().lower()
            if normalized in KEYWORDS_STOP_HEADINGS:
                break
            if NUMBERED_SECTION_HEADING.match(following_line):
                break
            section_lines.append(following_line.strip())

        while section_lines and not section_lines[-1]:
            section_lines.pop()

        if section_lines:
            keywords_text = " ".join(section_lines)
            keywords_raw = re.split(r"[,;]", keywords_text)
            keywords: list[str] = []
            for kw in keywords_raw:
                kw_cleaned = kw.strip()
                if kw_cleaned:
                    keywords.append(kw_cleaned)
            return keywords

        return []

    return []


TITLE_MAX_CHARS = 250
TITLE_MIN_WORDS = 2

TITLE_CONJUNCTIONS = (
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "under",
    "using",
    "via",
    "with",
)

EMAIL_TOKEN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

FRONT_MATTER_METADATA_LABEL = re.compile(
    r"^\s*(?:accepted|author contributions|available|citation|competing "
    r"interests|copyright|correspondence|data availability|doi|editor|"
    r"funding|index terms|keywords|license|licensed|orcid|published|"
    r"published online|received|retrieved|submitted)\s*:",
    re.IGNORECASE,
)

DECORATIVE_TITLE_LINES = (
    "brief report",
    "case report",
    "case study",
    "corrigendum",
    "erratum",
    "letter to the editor",
    "original article",
    "original research",
    "preprint",
    "research article",
    "review article",
    "study protocol",
)

BRACKETED_REFERENCE = re.compile(r"^\s*\[\s*(\d{1,4})\s*\]\s*(.*)$")
NUMERAL_REFERENCE = re.compile(r"^\s*(\d{1,4})[.)]\s*(.*)$")
BARE_NUMBER = re.compile(r"^\s*(\d{1,4})[.)]?\s*$")
BARE_DIGITS_ONLY = re.compile(r"^\s*(\d{1,4})\s*$")

PAREN_YEAR = re.compile(r"\(\s*((?:1[89]|20)\d{2})[a-z]?\s*\)")
BARE_YEAR = re.compile(r"\b((?:1[89]|20)\d{2})[a-z]?\b")
URL_TOKEN = re.compile(r"https?://\S+")
DOI_TOKEN = re.compile(r"\b10\.\d{4,9}/[^\s.,;:!?)]+")
AUTHOR_LIKE_START = re.compile(
    r"^\s*(?:[A-Z\u00C0-\u024F]|"
    r"(?:van|van der|van den|de|den|der|von|la|le|d')\s+[A-Z\u00C0-\u024F])"
)
WRAPPED_YEAR_START = re.compile(r"^\s*\(\s*((?:1[89]|20)\d{2})[a-z]?\s*\)")
AUTHORISH_LINE_END = re.compile(r"(?:[A-Z\u00C0-\u024F]\.|[,&])\s*$")
HEADER_FOOTER_START = re.compile(
    r"^\s*(?:vol\.?|no\.?|pp?\.|page\b|retrieved\b|available\b|accessed\b|cited\b)",
    re.IGNORECASE,
)

UNRELIABLE_WARNING = (
    "Reference splitting unreliable: references do not follow a numbered or "
    "author-year style."
)
NUMBERING_GAP_WARNING = (
    "Reference splitting detected numbering gaps; entries may be incomplete."
)
AUTHOR_YEAR_FALLBACK_WARNING = (
    "Structured references were extracted using conservative author-year fallback."
)
LOW_CONFIDENCE_AUTHOR_YEAR_WARNING = (
    "Author-year splitting produced low-confidence results; references may be incomplete."
)
UNASSIGNED_TEXT_WARNING = (
    "Some reference text could not be assigned to a reference entry."
)
TITLE_UNCERTAIN_WARNING = (
    "Title detection uncertain: no reliable title found before the abstract section."
)
AUTHOR_UNCERTAIN_WARNING = (
    "Author detection uncertain: no trustworthy authors could be identified "
    "in the front matter."
)


def _looks_like_prose(line: str) -> bool:
    """True when a line reads like running text rather than a title."""
    words = re.findall(r"[^\W\d_]+", line)
    if len(words) < 8:
        return False
    lowercase_starting = sum(1 for word in words if word[0].islower())
    return lowercase_starting >= max(3, len(words) // 2)


def _is_journal_header(line: str) -> bool:
    """True when a line is a journal banner or publishing artifact."""
    for pattern in JOURNAL_HEADER_PATTERNS:
        if pattern.match(line):
            return True
    if STANDALONE_PAGE_NUMBER.match(line):
        return True
    return False


def _is_title_continuation(line: str, previous_line: str = "") -> bool:
    """True when a line clearly continues the title on the previous line."""
    stripped = line.strip()
    if not stripped or len(stripped) > TITLE_MAX_CHARS // 2:
        return False
    if not stripped[0].isalpha():
        return False
    if FRONT_MATTER_METADATA_LABEL.match(stripped):
        return False
    if HEADER_FOOTER_START.match(stripped):
        return False
    if _is_journal_header(stripped):
        return False
    if stripped.lower() in DECORATIVE_TITLE_LINES:
        return False
    if (
        URL_TOKEN.search(stripped)
        or DOI_TOKEN.search(stripped)
        or EMAIL_TOKEN.search(stripped)
        or "orcid" in stripped.lower()
        or IEEE_MEMBERSHIP_PATTERN.search(stripped)
    ):
        return False

    first = stripped.split()[0]
    if first[0].islower() or first.lower() in TITLE_CONJUNCTIONS:
        return True

    # Multi-line title continuation in all-caps or title-case
    if previous_line and (previous_line.isupper() and stripped.isupper()):
        return True
    if previous_line and previous_line.endswith((":", "-", "–")):
        return True

    return False


def _is_plausible_title_line(line: str) -> bool:
    """True when a front-matter line plausibly forms an academic title."""
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > TITLE_MAX_CHARS:
        return False
    if not (stripped[0].isalpha() and (stripped[0].isupper() or stripped.isupper())):
        return False
    if _is_journal_header(stripped):
        return False
    lowered = stripped.lower()
    if lowered in DECORATIVE_TITLE_LINES:
        return False
    if FRONT_MATTER_METADATA_LABEL.match(stripped):
        return False
    if HEADER_FOOTER_START.match(stripped):
        return False
    if (
        URL_TOKEN.search(stripped)
        or DOI_TOKEN.search(stripped)
        or EMAIL_TOKEN.search(stripped)
        or IEEE_MEMBERSHIP_PATTERN.search(stripped)
    ):
        return False
    if "orcid" in lowered or "copyright" in lowered or "all rights reserved" in lowered:
        return False
    if "\u00a9" in stripped:
        return False
    words = [word for word in re.split(r"\s+", stripped) if re.search(r"[^\W\d_]", word)]
    if len(words) < TITLE_MIN_WORDS:
        return False
    return not _looks_like_prose(stripped)


def _detect_title(front_matter: list[str]) -> tuple[str | None, list[str]]:
    """Conservatively infer a paper title from the front matter."""
    clean_front = [l for l in front_matter if not _is_journal_header(l)]
    for index, line in enumerate(clean_front):
        if not _is_plausible_title_line(line):
            continue
        parts = [line.strip()]
        total = len(parts[0])
        prev = line.strip()
        for continuation in clean_front[index + 1 :]:
            if not _is_title_continuation(continuation, prev):
                break
            candidate_total = total + 1 + len(continuation.strip())
            if candidate_total > TITLE_MAX_CHARS:
                break
            parts.append(continuation.strip())
            total = candidate_total
            prev = continuation.strip()
            # Stop if the continuation line ended naturally with period or colon
            if continuation.strip().endswith("."):
                break
        return " ".join(parts), []

    if not clean_front:
        return None, []
    return None, [TITLE_UNCERTAIN_WARNING]


AUTHOR_SEPARATOR = re.compile(r"\s+(?:and|&)\s+", re.IGNORECASE)
SUPERSCRIPT_SUFFIX = re.compile(r"\d+(?:,\d+)*$")
ACRONYM_WORD = re.compile(r"^[A-Z]{3,}$")
NAME_WORD = re.compile(
    r"^(?:[A-Z\u00C0-\u024F][\w'\u00C0-\u024F-]*|[A-Z\u00C0-\u024F]\.)$"
)
INITIALS_NAME = re.compile(
    r"^[A-Z\u00C0-\u024F][\w'\u00C0-\u024F-]*,\s*"
    r"[A-Z\u00C0-\u024F]\.(?:\s*[A-Z\u00C0-\u024F]\.)*"
    r"(?:\d+(?:,\d+)*)?$"
)
AUTHOR_PARTICLES = (
    "de",
    "del",
    "della",
    "delle",
    "den",
    "der",
    "du",
    "la",
    "le",
    "ten",
    "ter",
    "van",
    "von",
)


def _find_title_span(front_matter: list[str]) -> tuple[int, int] | None:
    """Locate ``(start, end)`` of the title block."""
    for index, line in enumerate(front_matter):
        if not _is_plausible_title_line(line):
            continue
        total = len(line.strip())
        end = index + 1
        prev = line.strip()
        for continuation in front_matter[index + 1 :]:
            if not _is_title_continuation(continuation, prev):
                break
            candidate_total = total + 1 + len(continuation.strip())
            if candidate_total > TITLE_MAX_CHARS:
                break
            total = candidate_total
            end += 1
            prev = continuation.strip()
        return index, end
    return None


def _clean_author_name(name: str) -> str:
    """Clean and normalize author casing (e.g. 'KANG G. SHIN' -> 'Kang G. Shin')."""
    words = name.split()
    cleaned_words: list[str] = []
    for w in words:
        if w.endswith("."):
            cleaned_words.append(w.upper())
        elif w.isupper() and len(w) > 1:
            cleaned_words.append(w.capitalize())
        else:
            cleaned_words.append(w)
    return " ".join(cleaned_words)


def _is_given_name_token(token: str) -> bool:
    """True when a token looks like a 2-5 word human name."""
    candidate = token[:-1].strip() if token.endswith(".") else token
    if not candidate:
        return False
    words = candidate.split()
    if not 2 <= len(words) <= 5:
        return False

    capitalized = 0
    has_plain_word = False
    for word in words:
        if word.lower() in AUTHOR_PARTICLES:
            continue
        if word.endswith("."):
            capitalized += 1
            continue
        if word.isalpha() and (word.istitle() or (word.isupper() and len(word) <= 15)):
            capitalized += 1
            has_plain_word = True
            continue
        return False

    return capitalized >= 2 and has_plain_word


def _extract_author_pieces(line: str) -> list[str]:
    """Split a candidate author line into validated name pieces."""
    # 1. Strip IEEE membership designations
    clean_line = IEEE_MEMBERSHIP_PATTERN.sub("", line)
    clean_line = re.sub(r"\b(?:FELLOW|MEMBER|SENIOR MEMBER)\b", "", clean_line, flags=re.IGNORECASE)

    pieces: list[str] = []
    for group in AUTHOR_SEPARATOR.split(clean_line):
        group = group.strip().rstrip(",")
        if not group:
            continue
        if INITIALS_NAME.match(group):
            pieces.append(_clean_author_name(SUPERSCRIPT_SUFFIX.sub("", group).rstrip(" ,")))
            continue
        for token in group.split(","):
            token = token.strip()
            if not token:
                continue
            token = " ".join(SUPERSCRIPT_SUFFIX.sub("", word) for word in token.split())
            if _is_given_name_token(token):
                pieces.append(_clean_author_name(token))
    return pieces


def _detect_authors(front_matter: list[str]) -> tuple[list[str], list[str]]:
    """Conservatively infer author names from the front matter."""
    if not front_matter:
        return [], []
    span = _find_title_span(front_matter)
    region = front_matter[span[1] :] if span else front_matter

    authors: list[str] = []
    seen: set[str] = set()
    for line in region:
        stripped = line.strip()
        if not stripped:
            continue
        if _is_journal_header(stripped):
            continue
        lowered = stripped.lower()
        if (
            EMAIL_TOKEN.search(stripped)
            or URL_TOKEN.search(stripped)
            or DOI_TOKEN.search(stripped)
            or "orcid" in lowered
            or "\u00a9" in stripped
            or "copyright" in lowered
            or "all rights reserved" in lowered
        ):
            continue
        if FRONT_MATTER_METADATA_LABEL.match(stripped):
            continue
        if HEADER_FOOTER_START.match(stripped):
            continue
        if not stripped[:1].isalpha():
            continue
        affiliation_line = re.sub(r"^\s*\d+[.)]?\s*", "", stripped).strip()
        if AFFILIATION_KEYWORDS.search(affiliation_line):
            continue
        for piece in _extract_author_pieces(stripped):
            if piece.lower() in seen:
                continue
            seen.add(piece.lower())
            authors.append(piece)

    if authors:
        return authors, []
    if not region:
        return [], []
    return [], [AUTHOR_UNCERTAIN_WARNING]


AUTHOR_BIO_START = re.compile(
    r"^[A-Z][a-zA-Z\s.,-]+\((?:Fellow|Member|Senior Member|Student Member|Life Fellow),\s*IEEE\)\s+received\b",
    re.IGNORECASE,
)


def split_references(references_text: str) -> tuple[list[dict], list[str]]:
    """Split a references section into structured entries where possible."""
    if not references_text:
        return [], []

    raw_lines = [line for line in references_text.splitlines() if line.strip()]
    if not raw_lines:
        return [], []

    bio_stop = len(raw_lines)
    for i, l in enumerate(raw_lines):
        if AUTHOR_BIO_START.match(l) or l.lower() in ("biography", "biographies", "author biographies"):
            bio_stop = i
            break
    lines = raw_lines[:bio_stop]
    if not lines:
        return [], []

    numbered = split_numbered_references(lines)
    if numbered is not None:
        return numbered

    author_year = split_author_year_references(lines)
    if author_year is not None:
        return author_year

    return [], [UNRELIABLE_WARNING]
OCR_3DIGIT_RE = re.compile(
    r"^\s*[\[(]?\s*([1lI|])\s*([0oO\d])\s*([0oO\d])\s*([1lI\])])\s*(.*)$"
)
OCR_3DIGIT_SPACE_RE = re.compile(
    r"^\s*[\[(]?\s*([1lI])\s*(\d{2})\s*([1lI\])])\s*(.*)$"
)
OCR_2DIGIT_RE = re.compile(
    r"^\s*([1(\[])\s*(\d{2})\s*([1)\]])\s*([A-Z\"'‘“\-].*)$"
)


def _decode_ocr_char_digit(c: str) -> str:
    if c in ("l", "I", "|", "1"):
        return "1"
    if c in ("o", "O", "0"):
        return "0"
    return c


def detect_numbered_markers(
    lines: list[str],
) -> list[tuple[int, int, str | None, str]]:
    """Return ``(line_index, number, inline_content, style)`` for marker lines."""
    markers: list[tuple[int, int, str | None, str]] = []
    last_num = 0

    for index, line in enumerate(lines):
        match = BRACKETED_REFERENCE.match(line)
        if match:
            num = int(match.group(1))
            content = match.group(2).strip() or None
            markers.append((index, num, content, "bracket"))
            last_num = num
            continue
        match = NUMERAL_REFERENCE.match(line)
        if match:
            num = int(match.group(1))
            content = match.group(2).strip() or None
            markers.append((index, num, content, "numeral"))
            last_num = num
            continue
        match = BARE_NUMBER.match(line)
        if match:
            num = int(match.group(1))
            markers.append((index, num, None, "numeral"))
            last_num = num
            continue

        # Context-aware OCR repair for corrupted bracket markers inside reference section
        if last_num >= 20:
            m3 = OCR_3DIGIT_RE.match(line)
            if m3:
                d1 = _decode_ocr_char_digit(m3.group(1))
                d2 = _decode_ocr_char_digit(m3.group(2))
                d3 = _decode_ocr_char_digit(m3.group(3))
                if d1 == "1" and d2.isdigit() and d3.isdigit():
                    cand = int(d1 + d2 + d3)
                    if 0 < cand - last_num <= 5:
                        markers.append((index, cand, m3.group(5).strip() or None, "bracket_ocr"))
                        last_num = cand
                        continue

            m3s = OCR_3DIGIT_SPACE_RE.match(line)
            if m3s:
                d1 = _decode_ocr_char_digit(m3s.group(1))
                cand = int(d1 + m3s.group(2))
                if 0 < cand - last_num <= 5:
                    markers.append((index, cand, m3s.group(4).strip() or None, "bracket_ocr"))
                    last_num = cand
                    continue

            m2 = OCR_2DIGIT_RE.match(line)
            if m2:
                cand = int(m2.group(2))
                if 0 < cand - last_num <= 5:
                    markers.append((index, cand, m2.group(4).strip() or None, "bracket_ocr"))
                    last_num = cand
                    continue

    return markers


UNNUMBERED_AUTHOR_ENTRY_START = re.compile(
    r"^\s*(?:[A-Z](?:\.-?|\.)\s*(?:[A-Z](?:\.-?|\.)\s*)?[A-Z][a-zA-Z\u00C0-\u024F-]+|"
    r"__\s*,|"
    r"[A-Z]{3,}\s*,|"
    r"[A-Z][a-zA-Z\u00C0-\u024F-]+,\s+[A-Z]\.)",
)


def _split_unnumbered_author_entries(lines: list[str]) -> list[dict]:
    """Segment unnumbered reference lines by author boundaries (e.g. cropped margins)."""
    boundaries: list[int] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or _is_journal_header(stripped) or STANDALONE_PAGE_NUMBER.match(stripped):
            continue
        if UNNUMBERED_AUTHOR_ENTRY_START.match(stripped):
            boundaries.append(i)

    if len(boundaries) < 2:
        return []

    entries: list[dict] = []
    for pos, start in enumerate(boundaries):
        end = boundaries[pos + 1] if pos + 1 < len(boundaries) else len(lines)
        chunk_lines = [
            l.strip()
            for l in lines[start:end]
            if not _is_journal_header(l.strip()) and not STANDALONE_PAGE_NUMBER.match(l.strip())
        ]
        text = " ".join(l for l in chunk_lines if l)
        if len(text) >= 15:
            entries.append({"number": None, "raw_text": text})

    return entries


def split_numbered_references(
    lines: list[str],
) -> tuple[list[dict], list[str]] | None:
    """Split a numbered references section; ``None`` when not reliably numbered."""
    # Stop before trailing author biographies if present
    bio_stop = len(lines)
    for i, l in enumerate(lines):
        if AUTHOR_BIO_START.match(l) or l.lower() in ("biography", "biographies", "author biographies"):
            bio_stop = i
            break
    clean_lines = lines[:bio_stop]

    markers = detect_numbered_markers(clean_lines)
    if len(markers) < 2:
        return None

    # Filter out isolated non-bracket markers if mostly bracket style
    bracket_count = sum(1 for m in markers if "bracket" in m[3])
    if bracket_count >= len(markers) * 0.7:
        markers = [m for m in markers if "bracket" in m[3]]

    first_marker_index = markers[0][0]
    entries: list[dict] = []

    # Segment any preceding unnumbered reference blocks before the first numbered marker
    if first_marker_index > 0:
        preceding = clean_lines[:first_marker_index]
        author_entries = _split_unnumbered_author_entries(preceding)
        if author_entries:
            for pe in author_entries:
                entries.append(pe)
        else:
            ay_result = split_author_year_references(preceding)
            if ay_result is not None:
                preceding_entries, _ = ay_result
                for pe in preceding_entries:
                    entries.append({"number": None, "raw_text": pe["raw_text"]})

    current: dict | None = None
    marker_pos = 0

    for line_index in range(first_marker_index, len(clean_lines)):
        line = clean_lines[line_index].strip()
        is_marker = marker_pos < len(markers) and markers[marker_pos][0] == line_index
        if is_marker:
            _, number, content, _ = markers[marker_pos]
            marker_pos += 1
            if current is not None:
                entries.append(current)
            current = {"number": number, "raw_text": content or ""}
            continue

        if current is not None:
            sep = " " if current["raw_text"] else ""
            current["raw_text"] += sep + line

    if current is not None:
        entries.append(current)

    entries = [entry for entry in entries if len(entry["raw_text"]) >= 5]
    if not validate_reference_entries(entries):
        return None

    warnings: list[str] = []
    numbers = [e["number"] for e in entries if e.get("number") is not None]
    expected_count = max(numbers) if numbers else 0
    missing = set(range(1, expected_count + 1)) - set(numbers)
    if missing:
        warnings.append(NUMBERING_GAP_WARNING)

    _extract_entry_dois(entries)
    return entries, warnings


def validate_reference_numbering(entries: list[dict]) -> dict:
    """Discover reference sequence and calculate validation stats dynamically."""
    numbers = [entry["number"] for entry in entries if entry.get("number") is not None]
    highest_observed = max(numbers) if numbers else None
    detected_count = len(entries)
    observed_numbers = sorted(list(set(numbers)))

    if highest_observed is not None:
        missing_numbers = sorted(list(set(range(1, highest_observed + 1)) - set(numbers)))
    else:
        missing_numbers = []

    duplicate_numbers = sorted(list(set([n for n in numbers if numbers.count(n) > 1])))
    unnumbered_entries = sum(1 for entry in entries if entry.get("number") is None)
    malformed_count = sum(1 for entry in entries if len(entry.get("raw_text", "")) < 10)

    if highest_observed is not None and highest_observed > 0:
        missing_ratio = len(missing_numbers) / highest_observed
        if missing_ratio <= 0.05 and not duplicate_numbers:
            status = "good"
            certainty = "high"
        elif detected_count >= 5 and missing_ratio <= 0.35:
            status = "degraded"
            certainty = "medium"
        else:
            status = "degraded" if detected_count >= 10 else "poor"
            certainty = "low"
    else:
        status = "good" if entries else "poor"
        certainty = "low"

    return {
        "highest_observed_reference": highest_observed,
        "detected_reference_count": detected_count,
        "observed_numbers": observed_numbers,
        "missing_numbers": missing_numbers,
        "duplicate_numbers": duplicate_numbers,
        "unnumbered_entries": unnumbered_entries,
        "malformed_entries": malformed_count,
        "malformed_count": malformed_count,
        "reference_extraction_status": status,
        "numbering_certainty": certainty,
        "status": status,
        "expected_count": highest_observed or 0,
        "reference_count": detected_count,
    }


def _year_free_head(line: str, limit: int = 120) -> str:
    """First characters of a line with URLs and DOI tokens removed."""
    head = line[:limit]
    head = URL_TOKEN.sub(" ", head)
    head = DOI_TOKEN.sub(" ", head)
    return head


def _has_early_year(line: str, limit: int = 120) -> bool:
    """True when a 4-digit year appears early in the line (URL/DOI excluded)."""
    head = _year_free_head(line, limit)
    return bool(PAREN_YEAR.search(head) or BARE_YEAR.search(head))


def looks_like_author_year_start(line: str) -> bool:
    """True when a line plausibly starts an author-year reference entry."""
    if HEADER_FOOTER_START.match(line):
        return False
    if not AUTHOR_LIKE_START.match(line):
        return False
    return _has_early_year(line)


def split_author_year_references(
    lines: list[str],
) -> tuple[list[dict], list[str]] | None:
    """Split an author-year bibliography conservatively."""
    boundaries: list[int] = []
    for index, line in enumerate(lines):
        if looks_like_author_year_start(line):
            boundaries.append(index)
            continue
        if (
            index > 0
            and WRAPPED_YEAR_START.match(line)
            and AUTHORISH_LINE_END.search(lines[index - 1])
        ):
            boundaries.append(index - 1)

    if not boundaries:
        return None
    if boundaries[0] != 0:
        boundaries.insert(0, 0)

    entries: list[dict] = []
    for position, start in enumerate(boundaries):
        end = boundaries[position + 1] if position + 1 < len(boundaries) else len(lines)
        text = " ".join(line.strip() for line in lines[start:end]).strip()
        entries.append({"number": position + 1, "raw_text": text})

    if not validate_reference_entries(entries, require_years=True):
        return None

    _extract_entry_dois(entries)
    warnings = [AUTHOR_YEAR_FALLBACK_WARNING]
    with_year = sum(1 for entry in entries if _has_early_year(entry["raw_text"]))
    tiny = [entry for entry in entries if len(entry["raw_text"]) < 10]
    if with_year < len(entries) or tiny:
        warnings.append(LOW_CONFIDENCE_AUTHOR_YEAR_WARNING)
    return entries, warnings


def validate_reference_entries(entries: list[dict], *, require_years: bool = False) -> bool:
    """Reliability gate shared by numbered and author-year splitting."""
    if not entries:
        return False
    if len(entries) < (2 if require_years else 1):
        return False
    if any(not entry["raw_text"] for entry in entries):
        return False
    tiny = [entry for entry in entries if len(entry["raw_text"]) < 10]
    if len(tiny) > max(1, len(entries) // 5):
        return False
    if require_years:
        with_year = sum(1 for entry in entries if _has_early_year(entry["raw_text"]))
        if with_year < max(2, int(len(entries) * 0.6)):
            return False
    return True


def _extract_entry_dois(entries: list[dict]) -> None:
    """Attach the first DOI candidate of each entry as its ``doi``."""
    for entry in entries:
        candidates = extract_doi_candidates(entry["raw_text"])
        entry["doi"] = candidates[0] if candidates else None


def compute_extraction_quality(
    title: str | None,
    authors: list[str],
    abstract: str | None,
    abstract_status: str,
    references: list[dict],
    ref_validation: dict | None,
) -> dict:
    """Calculate extraction quality score (0.0 to 1.0), status, and issues."""
    issues: list[str] = []
    score = 0.0

    # Title check (max 0.25)
    if title:
        score += 0.25
    else:
        issues.append("Title could not be reliably extracted")

    # Author check (max 0.25)
    if authors:
        score += 0.25
    else:
        issues.append("Authors could not be reliably extracted")

    # Abstract check (max 0.25)
    if abstract_status == "found":
        score += 0.25
    elif abstract_status == "absent":
        score += 0.20
    else:  # uncertain
        score += 0.05
        issues.append("Abstract extraction uncertain or unverified")

    # Reference check (max 0.25)
    ref_status = (
        ref_validation.get("status", "good")
        if ref_validation
        else ("good" if references else "poor")
    )
    if ref_status == "good":
        score += 0.25
    elif ref_status == "degraded":
        score += 0.12
        missing = len(ref_validation.get("missing_numbers", [])) if ref_validation else 0
        issues.append(f"Reference extraction degraded ({missing} missing entries detected)")
    else:
        score += 0.0
        issues.append("Reference parsing failed or produced poor results")

    score = round(score, 2)
    if score >= 0.75:
        status = "good"
    elif score >= 0.40:
        status = "degraded"
    else:
        status = "poor"

    return {
        "quality_score": score,
        "status": status,
        "issues": issues,
    }


def extract_page_text_layout_aware(page: fitz.Page) -> str:
    """Extract page text preserving two-column reading order when detected."""
    try:
        blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    except Exception:
        return page.get_text("text")

    if not blocks:
        return ""

    page_width = page.rect.width
    mid = page_width / 2.0

    left_blocks = [b for b in blocks if b[2] <= mid + 25]
    right_blocks = [b for b in blocks if b[0] >= mid - 25]
    span_blocks = [b for b in blocks if b[0] < mid - 25 and b[2] > mid + 25]

    if len(left_blocks) >= 2 and len(right_blocks) >= 2:
        top_y_limit = min(left_blocks[0][1], right_blocks[0][1]) + 50
        top_spanning = sorted(
            [b for b in span_blocks if b[1] < top_y_limit],
            key=lambda b: (b[1], b[0]),
        )
        bottom_spanning = sorted(
            [b for b in span_blocks if b not in top_spanning],
            key=lambda b: (b[1], b[0]),
        )
        ordered = (
            top_spanning
            + sorted(left_blocks, key=lambda b: (b[1], b[0]))
            + sorted(right_blocks, key=lambda b: (b[1], b[0]))
            + bottom_spanning
        )
        return "\n".join(b[4].strip() for b in ordered)

    # Single-column fallback
    ordered = sorted(blocks, key=lambda b: (b[1], b[0]))
    return "\n".join(b[4].strip() for b in ordered)


def parse_pdf_bytes(data: bytes, filename: str) -> ExtractedPaper:
    """Parse a PDF given as an in-memory byte buffer."""
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except fitz.FileDataError as exc:
        raise PDFCorruptError(f"Could not open PDF '{filename}': {exc}") from exc
    except Exception as exc:
        raise PDFParseError(f"Unexpected error while opening PDF '{filename}': {exc}") from exc

    if document.needs_pass:
        document.close()
        raise PDFPasswordProtectedError(f"PDF '{filename}' is password-protected and cannot be read.")

    warnings: list[str] = []
    pages: list[dict] = []
    page_texts: list[str] = []
    page_count = document.page_count

    for page_number in range(page_count):
        try:
            page = document.load_page(page_number)
            raw_page_text = extract_page_text_layout_aware(page)
            text = normalize_pdf_text(raw_page_text)
        except Exception as exc:  # pragma: no cover - defensive
            text = ""
            warnings.append(f"Could not read text from page {page_number + 1}: {exc}")
        pages.append({"page_number": page_number + 1, "text": text})
        page_texts.append(text)

    document.close()

    raw_text = "\n".join(page_texts)
    if not raw_text.strip():
        raise PDFParseError(f"PDF '{filename}' contains no extractable text.")

    doi_candidates = extract_doi_candidates(raw_text)
    best_doi = None
    if doi_candidates:
        first_page = pages[0]["text"] if pages else ""
        header_text = first_page.split("\n", 20)
        header_candidates = [c for c in doi_candidates if any(c in line for line in header_text)]
        best_doi = header_candidates[0] if header_candidates else doi_candidates[0]

    lines = [line for line in raw_text.splitlines() if line.strip()]

    # Front-matter extraction first (title & authors)
    abstract_matches = _lines_with_heading(lines, ABSTRACT_HEADINGS)
    if abstract_matches:
        front_matter = lines[: abstract_matches[0][0]]
    else:
        abs_idx = None
        for i, l in enumerate(lines[:50]):
            if ABSTRACT_EM_DASH_PATTERN.match(l) or SPACED_ABSTRACT_PATTERN.match(l):
                abs_idx = i
                break

        intro_idx = None
        for i, line in enumerate(lines[:50]):
            norm = line.strip().rstrip(":").lower()
            if (
                norm in ("introduction", "1. introduction", "1 introduction", "i. introduction")
                or (NUMBERED_SECTION_HEADING.match(line) and "introduction" in norm)
            ):
                intro_idx = i
                break

        if abs_idx is not None:
            front_matter = lines[:abs_idx]
        elif intro_idx is not None:
            front_matter = lines[:intro_idx]
        else:
            front_matter = []

    title, title_warnings = _detect_title(front_matter)
    warnings.extend(title_warnings)
    title_confidence = 0.95 if title else None
    title_source = "front_matter" if title else None

    authors, author_warnings = _detect_authors(front_matter)
    warnings.extend(author_warnings)
    author_confidence = 0.90 if authors else None
    author_source = "front_matter" if authors else None

    # Abstract detection with status and author contamination validation
    abstract, abstract_status, abstract_confidence = _detect_abstract_detailed(lines, authors=authors)
    keywords = _detect_keywords(lines)
    references_text = _detect_references(lines)
    references: list[dict] = []
    ref_validation = None
    if references_text:
        references, split_warnings = split_references(references_text)
        warnings.extend(split_warnings)
        if references:
            ref_validation = validate_reference_numbering(references)

    if not doi_candidates:
        warnings.append("No DOI candidates found in the document.")
    if abstract_status == "uncertain":
        warnings.append("No abstract section detected.")
    if not references_text:
        warnings.append("No references section detected.")

    extraction_quality = compute_extraction_quality(
        title=title,
        authors=authors,
        abstract=abstract,
        abstract_status=abstract_status,
        references=references,
        ref_validation=ref_validation,
    )

    return ExtractedPaper(
        filename=filename,
        file_size_bytes=len(data),
        page_count=page_count,
        pages=pages,
        raw_text=raw_text,
        doi_candidates=doi_candidates,
        best_doi=best_doi,
        abstract=abstract,
        abstract_status=abstract_status,
        abstract_confidence=abstract_confidence,
        title=title,
        title_confidence=title_confidence,
        title_source=title_source,
        authors=authors,
        author_confidence=author_confidence,
        author_source=author_source,
        keywords=keywords,
        references_text=references_text,
        references=references,
        reference_validation=ref_validation,
        extraction_quality=extraction_quality,
        warnings=warnings,
    )
