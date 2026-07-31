"""PDF parsing service built on PyMuPDF.

Extracts raw text, page-wise text, DOI candidates, abstract and references
sections from an in-memory PDF byte buffer. The parsing is intentionally
heuristic and modular: title/author and advanced section detection can be
added later without touching the route layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
DOI_TRAILING_PUNCTUATION = ".,;:!?)]}"

ABSTRACT_HEADINGS = ("abstract", "summary")
ABSTRACT_STOP_HEADINGS = ("introduction", "keywords", "index terms", "1. introduction", "1 introduction")

REFERENCES_HEADINGS = ("references", "bibliography")


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
    lines: list[str], start_index: int, stop_headings: tuple[str, ...]
) -> str:
    """Join lines from start_index until a stop heading is found.

    Returns the section text, or ``None`` when nothing usable follows.
    """
    collected: list[str] = []
    for line in lines[start_index + 1 :]:
        stripped = line.strip().rstrip(":").lower()
        if stripped in stop_headings:
            break
        collected.append(line.strip())
    while collected and not collected[-1]:
        collected.pop()
    return "\n".join(collected).strip() or None


def _detect_abstract(lines: list[str]) -> str | None:
    """Find the abstract section between Abstract/Summary and a stop heading."""
    for index, _, _ in _lines_with_heading(lines, ABSTRACT_HEADINGS):
        section = _section_between(lines, index, ABSTRACT_STOP_HEADINGS)
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


BRACKETED_REFERENCE = re.compile(r"^\s*\[(\d+)\]\s*(.+)$")
NUMERAL_REFERENCE = re.compile(r"^\s*(\d{1,4})[.)]\s*(.+)$")


def split_references(references_text: str) -> tuple[list[dict], list[str]]:
    """Split references text into numbered entries where possible.

    Supports ``[1] text`` and ``1. text`` (or ``1) text``) styles.
    Returns (entries, warnings). When the style is ambiguous or
    unreliably detected, returns an empty entry list plus a warning
    instead of fabricating entries.
    """
    if not references_text:
        return [], []

    lines = [line for line in references_text.splitlines() if line.strip()]
    if not lines:
        return [], []

    style: str | None = None
    entries: list[dict] = []
    current: dict | None = None
    expected_number = 1

    for line in lines:
        bracket = BRACKETED_REFERENCE.match(line)
        numeral = NUMERAL_REFERENCE.match(line)

        candidate_style = None
        number: int | None = None
        content: str | None = None
        if bracket:
            candidate_style = "bracket"
            number = int(bracket.group(1))
            content = bracket.group(2)
        elif numeral:
            candidate_style = "numeral"
            number = int(numeral.group(1))
            content = numeral.group(2)

        if candidate_style is not None and number == expected_number and content:
            if style is None:
                style = candidate_style
            if candidate_style != style:
                return [], ["Reference splitting stopped: mixed numbering styles detected."]
            if current is not None:
                entries.append(current)
            current = {"number": number, "raw_text": content, "doi": None}
            expected_number += 1
        elif current is not None:
            current["raw_text"] += " " + line.strip()
        else:
            return [], ["Reference splitting unreliable: references do not follow a numbered style."]

    if current is not None:
        entries.append(current)

    if not entries:
        return [], ["Reference splitting unreliable: no numbered entries found."]

    for entry in entries:
        candidates = extract_doi_candidates(entry["raw_text"])
        entry["doi"] = candidates[0] if candidates else None

    return entries, []


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
    references_text = _detect_references(lines)
    references: list[dict] = []
    if references_text:
        references, split_warnings = split_references(references_text)
        warnings.extend(split_warnings)

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
        references_text=references_text,
        references=references,
        warnings=warnings,
    )
