"""PDF parsing service built on PyMuPDF.

Extracts raw text, page-wise text, DOI candidates, title, authors, abstract
and references sections from an in-memory PDF byte buffer. The parsing is
intentionally heuristic and modular, so sections can be extended without
touching the route layer.
"""

from __future__ import annotations

import re
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
)
ABSTRACT_STOP_COLON_PATTERN = re.compile(
    r"^\s*(?:accepted|citation|funding|index terms|keywords|received)\s*:",
    re.IGNORECASE,
)

REFERENCES_HEADINGS = ("references", "bibliography")
KEYWORDS_HEADINGS = ("keywords", "index terms")

KEYWORDS_STOP_HEADINGS = (
    "1. introduction",
    "1 introduction",
    "2. introduction",
    "2 introduction",
    "introduction",
    "1. method",
    "1 method",
    "2. method",
    "2 method",
    "method",
    "abstract",
    "references",
)

# Pattern to detect numbered/lettered section headings (e.g. "1. Introduction", "A. Background")
NUMBERED_SECTION_HEADING = re.compile(
    r"^\s*(?:\d{1,2}|[A-Z])\.?\s+[A-Z]",
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
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    references_text: str | None = None
    references: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _clean_doi(candidate: str) -> str:
    """Strip trailing punctuation from a raw DOI candidate."""
    return candidate.rstrip(DOI_TRAILING_PUNCTUATION)


def extract_doi_candidates(text: str) -> list[str]:
    """Return deduplicated, case-normalized DOI candidates from text.

    Trailing punctuation (e.g. ``.`` or ``)`` after a DOI) is removed.
    """
    candidates: list[str] = []
    seen: set[str] = set()
    for match in DOI_PATTERN.findall(text):
        cleaned = _clean_doi(match)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            candidates.append(cleaned)
    return candidates


def _lines_with_heading(lines: list[str], headings: tuple[str, ...]) -> list[tuple[int, str, str]]:
    """Return (index, matched heading, heading line) for lines matching a heading.

    A heading is a line whose stripped lowercase form equals one of the
    supplied headings, optionally followed by a colon.
    """
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
    """Join lines from start_index until a stop heading is found.

    Stops at a bare stop heading (optionally ending with a colon, matched
    case-insensitively and whitespace-tolerantly) or, when
    ``stop_colon_pattern`` is supplied, at a line headed by a colon-prefixed
    metadata label such as ``Funding: ...``. Colon labels are matched
    structurally, so prose such as ``Received wisdom ...`` is never a stop.
    Returns the section text, or ``None`` when nothing usable follows.
    """
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


def _detect_abstract(lines: list[str]) -> str | None:
    """Find the abstract section between Abstract/Summary and a stop heading."""
    for index, _, _ in _lines_with_heading(lines, ABSTRACT_HEADINGS):
        section = _section_between(
            lines, index, ABSTRACT_STOP_HEADINGS, ABSTRACT_STOP_COLON_PATTERN
        )
        if section:
            return section
    return None


def _detect_references(lines: list[str]) -> str | None:
    """Find the references section starting at the References heading."""
    for index, _, _ in _lines_with_heading(lines, REFERENCES_HEADINGS):
        section = _section_between(lines, index, ())
        if section:
            return section
    return None


def _detect_keywords(lines: list[str]) -> list[str]:
    """Extract keywords from the Keywords or Index Terms section.

    Searches for lines starting with "Keywords:" or "Index Terms:" (case-insensitive),
    then extracts all text until a numbered heading or major section appears.
    Handles both inline keywords (on the same line as the heading) and
    multi-line keywords. Keywords are cleaned and split by comma or semicolon.
    Returns an empty list if no keywords found.
    """
    keywords_heading_pattern = re.compile(r"^\s*(?:keywords|index terms)\s*:", re.IGNORECASE)
    
    for index, line in enumerate(lines):
        if not keywords_heading_pattern.match(line):
            continue
        
        # Extract content after the colon on the same line
        colon_pos = line.lower().find(":")
        inline_content = ""
        if colon_pos != -1:
            inline_content = line[colon_pos + 1:].strip()
        
        # Collect lines until a stop heading is found
        section_lines: list[str] = []
        if inline_content:
            section_lines.append(inline_content)
        
        for following_line in lines[index + 1 :]:
            normalized = following_line.strip().rstrip(":").strip().lower()
            # Stop at major section headings
            if normalized in KEYWORDS_STOP_HEADINGS:
                break
            # Stop at bare numbered headings like "1." or "A."
            if NUMBERED_SECTION_HEADING.match(following_line):
                break
            section_lines.append(following_line.strip())
        
        # Remove trailing empty lines
        while section_lines and not section_lines[-1]:
            section_lines.pop()
        
        if section_lines:
            # Join all lines and split by comma or semicolon
            keywords_text = " ".join(section_lines)
            keywords_raw = re.split(r"[,;]", keywords_text)
            keywords: list[str] = []
            for kw in keywords_raw:
                kw_cleaned = kw.strip()
                if kw_cleaned:
                    keywords.append(kw_cleaned)
            return keywords
        
        # Keywords section found but empty
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


BRACKETED_REFERENCE = re.compile(r"^\s*\[(\d+)\]\s*(.+)$")
NUMERAL_REFERENCE = re.compile(r"^\s*(\d{1,4})[.)]\s*(.+)$")
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

MAX_NUMBERING_GAP = 3
YEAR_WINDOW = 120
MIN_ENTRY_CHARS = 10
MIN_TINY_FRAGMENT_CHARS = 10

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
    """True when a line reads like running text rather than a title.

    Only lines with enough word tokens (likely a sentence) and a majority
    of lowercase-initiated words are classified as prose; short title lines
    are never rejected this way.
    """
    words = re.findall(r"[^\W\d_]+", line)
    if len(words) < 8:
        return False
    lowercase_starting = sum(1 for word in words if word[0].islower())
    return lowercase_starting >= max(3, len(words) // 2)


def _is_title_continuation(line: str) -> bool:
    """True when a line clearly continues the title on the previous line.

    Continuations start with a lowercase word (wrapped titles) or with a
    quiet title conjunction such as ``and`` / ``with``. Identifier,
    metadata and decorative lines are never continuations.
    """
    stripped = line.strip()
    if not stripped or len(stripped) > TITLE_MAX_CHARS // 2:
        return False
    if not stripped[0].isalpha():
        return False
    if FRONT_MATTER_METADATA_LABEL.match(stripped):
        return False
    if HEADER_FOOTER_START.match(stripped):
        return False
    if stripped.lower() in DECORATIVE_TITLE_LINES:
        return False
    if (
        URL_TOKEN.search(stripped)
        or DOI_TOKEN.search(stripped)
        or EMAIL_TOKEN.search(stripped)
        or "orcid" in stripped.lower()
    ):
        return False
    first = stripped.split()[0]
    return first[0].islower() or first.lower() in TITLE_CONJUNCTIONS


def _is_plausible_title_line(line: str) -> bool:
    """True when a front-matter line plausibly forms an academic title.

    Conservative by design: rejects metadata labels, decorative article
    labels, headers/footers, DOI/URL/email/ORCID identifiers, copyright
    notices, digit-led lines, implausible shapes and implied-prose
    sentences. Matching text is preserved verbatim.
    """
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > TITLE_MAX_CHARS:
        return False
    if not (stripped[0].isalpha() and stripped[0].isupper()):
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
    """Conservatively infer a paper title from the front matter.

    Prefers the first plausible title line and quietly joins an immediately
    following line that clearly continues the title (wrapped titles).
    Never fabricates a title: when nothing reliable is found a hedged
    warning is returned instead. ``None`` without a warning means the front
    matter was empty and nothing was claimed at all.
    """
    for index, line in enumerate(front_matter):
        if not _is_plausible_title_line(line):
            continue
        parts = [line.strip()]
        total = len(parts[0])
        for continuation in front_matter[index + 1 :]:
            if not _is_title_continuation(continuation):
                break
            candidate_total = total + 1 + len(continuation.strip())
            if candidate_total > TITLE_MAX_CHARS:
                break
            parts.append(continuation.strip())
            total = candidate_total
            if not continuation[0].islower():
                break
        return " ".join(parts), []
    if not front_matter:
        return None, []
    return None, [TITLE_UNCERTAIN_WARNING]


AUTHOR_SEPARATOR = re.compile(r"\s+(?:and|&)\s+")
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
AFFILIATION_KEYWORDS = re.compile(
    r"\b(?:academy|association|clinic|college|consortium|council|corporation|"
    r"department|division|faculty|foundation|group|hospital|incorporated|"
    r"institute|laborator(?:y|ies)|medical|polytechnic|school|society|unit|"
    r"university|centre|center)\b",
    re.IGNORECASE,
)


def _find_title_span(front_matter: list[str]) -> tuple[int, int] | None:
    """Locate ``(start, end)`` of the title block, mirroring ``_detect_title``."""
    for index, line in enumerate(front_matter):
        if not _is_plausible_title_line(line):
            continue
        total = len(line.strip())
        end = index + 1
        for continuation in front_matter[index + 1:]:
            if not _is_title_continuation(continuation):
                break
            candidate_total = total + 1 + len(continuation.strip())
            if candidate_total > TITLE_MAX_CHARS:
                break
            total = candidate_total
            end += 1
            if not continuation[0].islower():
                break
        return index, end
    return None


def _is_given_name_token(token: str) -> bool:
    """True when a token looks like a 2-5 word capitalized human name."""
    candidate = token[:-1].strip() if token.endswith(".") else token
    if not candidate:
        return False
    words = candidate.split()
    if not 2 <= len(words) <= 5:
        return False
    capitalized = 0
    has_plain_word = False
    for word in words:
        if ACRONYM_WORD.match(word):
            return False
        if NAME_WORD.match(word):
            capitalized += 1
            if not word.endswith("."):
                has_plain_word = True
            continue
        if word.lower() in AUTHOR_PARTICLES:
            continue
        return False
    return capitalized >= 2 and has_plain_word


def _extract_author_pieces(line: str) -> list[str]:
    """Split a candidate author line into validated name pieces."""
    pieces: list[str] = []
    for group in AUTHOR_SEPARATOR.split(line):
        group = group.strip().rstrip(",")
        if not group:
            continue
        if INITIALS_NAME.match(group):
            pieces.append(SUPERSCRIPT_SUFFIX.sub("", group).rstrip(" ,"))
            continue
        for token in group.split(","):
            token = token.strip()
            if not token:
                continue
            token = " ".join(SUPERSCRIPT_SUFFIX.sub("", word) for word in token.split())
            if _is_given_name_token(token):
                pieces.append(token)
    return pieces


def _detect_authors(front_matter: list[str]) -> tuple[list[str], list[str]]:
    """Conservatively infer author names from the front matter.

    The author region is anchored on the detected title block (or the whole
    front matter when no title could be found). Affiliation lines, emails,
    URLs, DOIs, ORCID identifiers, metadata labels, headers/footers and
    affiliation-numbered lines are ignored. Names must match either a
    ``Surname, J. R.`` initials form or a 2-5 word capitalized name; author
    order is preserved and duplicates are removed case-insensitively. Never
    fabricates an author: an empty result on a non-empty region yields one
    hedged warning, while an empty region yields no warning at all.
    """
    if not front_matter:
        return [], []
    span = _find_title_span(front_matter)
    region = front_matter[span[1]:] if span else front_matter

    authors: list[str] = []
    seen: set[str] = set()
    for line in region:
        stripped = line.strip()
        if not stripped:
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


def split_references(references_text: str) -> tuple[list[dict], list[str]]:
    """Split a references section into structured entries where possible.

    Supported styles:

    * numbered ``[1] text``, ``1. text`` and ``1) text`` (marker and body on
      the same line);
    * numbered with the marker alone on its own line (hanging indent), e.g.
      ``1.`` / ``1`` followed by the entry body;
    * conservative author-year bibliographies, e.g. ``Smith, J. (2018). ...``
      or ``Martín-Martín, A., ... (2018). ...``.

    Returns ``(entries, warnings)``. When no style can be applied reliably,
    an empty entry list plus a warning is returned instead of fabricated
    entries. ``number`` carries the printed marker number for numbered
    styles and the 1-based position for author-year styles. ``doi`` is the
    first DOI candidate found inside the entry, never the paper's primary
    DOI.
    """
    if not references_text:
        return [], []

    lines = [line for line in references_text.splitlines() if line.strip()]
    if not lines:
        return [], []

    numbered = split_numbered_references(lines)
    if numbered is not None:
        return numbered

    author_year = split_author_year_references(lines)
    if author_year is not None:
        return author_year

    return [], [UNRELIABLE_WARNING]


def detect_numbered_markers(
    lines: list[str],
) -> list[tuple[int, int, str | None, str]]:
    """Return ``(line_index, number, inline_content, style)`` for marker lines.

    ``inline_content`` is the reference text following the marker on the same
    line, or ``None`` when the marker stands alone (hanging indent).
    Styles are ``bracket`` (``[1]``) and ``numeral`` (``1.``, ``1)``, bare
    ``1``).
    """
    markers: list[tuple[int, int, str | None, str]] = []
    for index, line in enumerate(lines):
        match = BRACKETED_REFERENCE.match(line)
        if match:
            markers.append((index, int(match.group(1)), match.group(2), "bracket"))
            continue
        match = NUMERAL_REFERENCE.match(line)
        if match:
            markers.append((index, int(match.group(1)), match.group(2), "numeral"))
            continue
        match = BARE_NUMBER.match(line)
        if match:
            markers.append((index, int(match.group(1)), None, "numeral"))
    return markers


def split_numbered_references(
    lines: list[str],
) -> tuple[list[dict], list[str]] | None:
    """Split a numbered references section; ``None`` when not reliably numbered.

    Markers must start at line 0 with number 1 and continue substantially
    sequentially (small gaps of up to three are tolerated with a warning).
    Bare digit lines are only treated as markers when they match the exact
    expected sequence, so stray page numbers are not misread as references.
    Markers without any body of their own are dropped.
    """
    markers = detect_numbered_markers(lines)
    if len(markers) < 2:
        return None
    styles = {style for _, _, _, style in markers}
    if len(styles) > 1:
        return None

    # Drop consecutive markers without any content of their own.
    kept: list[tuple[int, int, str | None]] = []
    for position, (index, number, content, _style) in enumerate(markers):
        next_index = markers[position + 1][0] if position + 1 < len(markers) else len(lines)
        following = lines[index + 1:next_index]
        has_body = content is not None or any(not BARE_NUMBER.match(line) for line in following)
        if has_body:
            kept.append((index, number, content))
    if not kept:
        return None
    if kept[0][0] != 0 or kept[0][1] != 1:
        return None

    entries: list[dict] = []
    current: dict | None = None
    expected = 1
    gaps = 0
    kept_position = 0
    unassigned = False

    for line_index, line in enumerate(lines):
        is_marker = kept_position < len(kept) and kept[kept_position][0] == line_index
        if is_marker:
            number, content = kept[kept_position][1], kept[kept_position][2]
            kept_position += 1
            bare = content is None and BARE_DIGITS_ONLY.match(line) is not None
            if number == expected or (
                not bare and expected < number <= expected + MAX_NUMBERING_GAP
            ):
                if number != expected:
                    gaps += 1
                if current is not None:
                    entries.append(current)
                current = {"number": number, "raw_text": content or ""}
                expected = number + 1
                continue
            # Out-of-sequence marker: the line becomes ordinary content below.

        if current is None:
            unassigned = True
            continue
        separator = " " if current["raw_text"] else ""
        current["raw_text"] += separator + line.strip()

    if current is not None:
        entries.append(current)

    entries = [entry for entry in entries if len(entry["raw_text"]) >= MIN_ENTRY_CHARS]
    if not validate_reference_entries(entries):
        return None

    warnings: list[str] = []
    if gaps:
        warnings.append(NUMBERING_GAP_WARNING)
    if unassigned:
        warnings.append(UNASSIGNED_TEXT_WARNING)
    _extract_entry_dois(entries)
    return entries, warnings


def _year_free_head(line: str, limit: int = YEAR_WINDOW) -> str:
    """First ``limit`` characters of a line with URLs and DOI tokens removed.

    Years embedded in URLs or DOI suffixes (e.g. ``10.1016/J.JOI.2017.06.005``)
    are artifacts, not publication years, so they must not drive boundary
    detection.
    """
    head = line[:limit]
    head = URL_TOKEN.sub(" ", head)
    head = DOI_TOKEN.sub(" ", head)
    return head


def _has_early_year(line: str, limit: int = YEAR_WINDOW) -> bool:
    """True when a 4-digit year appears early in the line (URL/DOI excluded)."""
    head = _year_free_head(line, limit)
    return bool(PAREN_YEAR.search(head) or BARE_YEAR.search(head))


def looks_like_author_year_start(line: str) -> bool:
    """True when a line plausibly starts an author-year reference entry.

    Requires an author-like capitalized start (or a lowercase Dutch/European
    surname prefix such as ``de Winter``) plus a 4-digit year inside the
    first ~120 characters after removing URL/DOI tokens. Running-page-header
    lines such as ``Vol. 9, No. 5; 2013`` are excluded.
    """
    if HEADER_FOOTER_START.match(line):
        return False
    if not AUTHOR_LIKE_START.match(line):
        return False
    return _has_early_year(line)


def split_author_year_references(
    lines: list[str],
) -> tuple[list[dict], list[str]] | None:
    """Split an author-year bibliography conservatively.

    A new entry starts at a line matching :func:`looks_like_author_year_start`,
    or at the line before a wrapped ``(YYYY).`` continuation (author list and
    year split across lines, e.g. ``Dowle, M., ... Parsonage, H.`` +
    ``(2018). data.table: ...``). Continuation lines are appended to the
    current entry until the next confident boundary. Returns ``None`` when
    the output would be unreliable: fewer than two entries, many tiny
    fragments, or most entries without a year.
    """
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
    tiny = [entry for entry in entries if len(entry["raw_text"]) < MIN_TINY_FRAGMENT_CHARS]
    if with_year < len(entries) or tiny:
        warnings.append(LOW_CONFIDENCE_AUTHOR_YEAR_WARNING)
    return entries, warnings


def validate_reference_entries(entries: list[dict], *, require_years: bool = False) -> bool:
    """Reliability gate shared by numbered and author-year splitting.

    Conservative: entries must carry meaningful text and must not degrade
    into many tiny fragments. With ``require_years``, most entries must
    contain a plausible 4-digit year (author-year bibliographies only).
    """
    if not entries:
        return False
    if len(entries) < (2 if require_years else 1):
        return False
    if any(not entry["raw_text"] for entry in entries):
        return False
    tiny = [entry for entry in entries if len(entry["raw_text"]) < MIN_TINY_FRAGMENT_CHARS]
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


def parse_pdf_bytes(data: bytes, filename: str) -> ExtractedPaper:
    """Parse a PDF given as an in-memory byte buffer.

    Raises:
        PDFPasswordProtectedError: if the PDF is encrypted.
        PDFCorruptError: if the PDF cannot be opened.
        PDFParseError: if the PDF has no extractable text.
    """
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
            text = document.load_page(page_number).get_text("text")
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

    abstract = _detect_abstract(lines)
    keywords = _detect_keywords(lines)
    references_text = _detect_references(lines)
    references: list[dict] = []
    if references_text:
        references, split_warnings = split_references(references_text)
        warnings.extend(split_warnings)

    title = None
    authors: list[str] = []
    abstract_matches = _lines_with_heading(lines, ABSTRACT_HEADINGS)
    if abstract_matches:
        front_matter = lines[: abstract_matches[0][0]]
        title, title_warnings = _detect_title(front_matter)
        warnings.extend(title_warnings)
        authors, author_warnings = _detect_authors(front_matter)
        warnings.extend(author_warnings)

    if not doi_candidates:
        warnings.append("No DOI candidates found in the document.")
    if not abstract:
        warnings.append("No abstract section detected.")
    if not references_text:
        warnings.append("No references section detected.")

    return ExtractedPaper(
        filename=filename,
        file_size_bytes=len(data),
        page_count=page_count,
        pages=pages,
        raw_text=raw_text,
        doi_candidates=doi_candidates,
        best_doi=best_doi,
        abstract=abstract,
        title=title,
        authors=authors,
        keywords=keywords,
        references_text=references_text,
        references=references,
        warnings=warnings,
    )
