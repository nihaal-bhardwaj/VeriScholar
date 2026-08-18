"""Local consistency rules engine for extracted research papers.

This module checks for internal inconsistencies inside a research paper.
It never calls any external API and only analyzes the extracted text
locally. Every flag is an explainable screening signal for human review,
never a fake-paper verdict.
"""

import re

from app.schemas.consistency import ConsistencyFlag, ConsistencyReport
from app.schemas.paper import ReferenceEntry

# RULE 1 — date consistency

_PAPER_YEAR_PATTERNS = [
    re.compile(r"\b(?:Received|Accepted)\s*:\s*(\d{4})\b", re.IGNORECASE),
    re.compile(r"\bPublished\s+(\d{4})\b", re.IGNORECASE),
    re.compile(r"\bCopyright\s*\(?c\)?\s*(\d{4})\b", re.IGNORECASE),
    re.compile(r"©\s*(\d{4})\b"),
]

_YEAR_RE = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2})\b")

# RULE 2 — figure reference consistency

_FIGURE_REF_RE = re.compile(r"\b(?:figure|fig\.?)\s*(\d+)\b", re.IGNORECASE)
_FIGURE_DEF_RE = re.compile(r"\b(?:figure|fig\.?)\s*(\d+)\s*:", re.IGNORECASE)

# RULE 3 — author name consistency

_NAME_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ'-]+")

# RULE 4 — section structure consistency

_STANDARD_SECTIONS = ["Abstract", "Introduction", "Conclusion", "References"]

# RULE 5 — reference number continuity

_CITATION_RE = re.compile(r"\[([0-9][0-9\s,\-]*)\]")

_MAX_EVIDENCE_CHARS = 200


def _snippet(text: str, start: int, end: int | None = None, width: int = 120) -> str:
    """Return a trimmed window of text around a match span."""
    end = start if end is None else end
    snippet_start = max(0, start - width // 2)
    snippet_end = min(len(text), end + width // 2)
    return text[snippet_start:snippet_end].strip()


def _find_paper_year(full_text: str, abstract: str | None = None) -> int | None:
    """Find the paper's publication year, or None when unknown.

    Checks explicit markers first ("Received: 2023", "Published 2022",
    "Copyright 2021", "(c) 2021", "© 2021"); falls back to the most
    recent year mentioned in the abstract when provided.
    """
    for pattern in _PAPER_YEAR_PATTERNS:
        match = pattern.search(full_text)
        if match:
            return int(match.group(1))
    if abstract:
        years = [int(y) for y in _YEAR_RE.findall(abstract)]
        if years:
            return max(years)
    return None


def _years_in_text(text: str) -> list[int]:
    """Return all plausible 4-digit years mentioned in the given text."""
    return [int(year) for year in _YEAR_RE.findall(text)]


def _check_date_consistency(
    full_text: str,
    abstract: str | None,
    references: list[ReferenceEntry],
    flags: list[ConsistencyFlag],
    passed: list[str],
) -> None:
    """Rule 1: a cited reference must not be newer than the paper itself."""
    paper_year = _find_paper_year(full_text, abstract)
    if paper_year is None:
        return

    issues = 0
    for reference in references:
        for year in _years_in_text(reference.raw_text):
            if year > paper_year:
                flags.append(
                    ConsistencyFlag(
                        rule="date_consistency",
                        severity="high",
                        message=(
                            f"Reference [{reference.number}] cites a paper from {year} "
                            f"which is after this paper's year {paper_year}"
                        ),
                        evidence=reference.raw_text[:_MAX_EVIDENCE_CHARS],
                    )
                )
                issues += 1
                break

    if issues == 0:
        passed.append(
            "date_consistency: all cited reference years are on or before "
            "the paper's publication year"
        )


def _check_figure_consistency(
    full_text: str,
    flags: list[ConsistencyFlag],
    passed: list[str],
) -> None:
    """Rule 2: every figure referenced in the text must also be defined."""
    defined = {int(match.group(1)) for match in _FIGURE_DEF_RE.finditer(full_text)}
    referenced = {int(match.group(1)) for match in _FIGURE_REF_RE.finditer(full_text)}
    missing = sorted(referenced - defined)

    if missing:
        for number in missing:
            match = next(
                m for m in _FIGURE_REF_RE.finditer(full_text) if int(m.group(1)) == number
            )
            flags.append(
                ConsistencyFlag(
                    rule="figure_reference_consistency",
                    severity="medium",
                    message=f"Figure {number} is referenced in text but never defined",
                    evidence=_snippet(full_text, match.start(), match.end()),
                )
            )
    else:
        passed.append(
            "figure_reference_consistency: every referenced figure is defined"
        )


def _last_name(name: str) -> str | None:
    """Return the last name of an author name string, or None."""
    tokens = _NAME_TOKEN_RE.findall(name)
    return tokens[-1] if tokens else None


def _check_author_consistency(
    full_text: str,
    authors: list[str],
    flags: list[ConsistencyFlag],
    passed: list[str],
) -> None:
    """Rule 3: every listed author's last name should appear in the text."""
    if not authors:
        return

    issues = 0
    for name in authors:
        last = _last_name(name)
        if last is None:
            continue
        if not re.search(rf"\b{re.escape(last)}\b", full_text, re.IGNORECASE):
            flags.append(
                ConsistencyFlag(
                    rule="author_name_consistency",
                    severity="medium",
                    message=(
                        f"Author '{name}' from author list not found anywhere in paper text"
                    ),
                    evidence=name,
                )
            )
            issues += 1

    if issues == 0:
        passed.append(
            "author_name_consistency: every listed author's last name appears "
            "in the paper text"
        )


def _check_section_structure(
    full_text: str,
    warnings: list[str],
    passed: list[str],
) -> None:
    """Rule 4: standard academic sections should exist (soft warning only)."""
    lines = full_text.splitlines()
    present: set[str] = set()
    for line in lines:
        for section in _STANDARD_SECTIONS:
            pattern = re.compile(
                rf"^\s*(?:\d+(?:\.\d+)*\.?\s+)?{re.escape(section)}\b",
                re.IGNORECASE,
            )
            if pattern.match(line):
                present.add(section.lower())

    for section in _STANDARD_SECTIONS:
        if section.lower() not in present:
            warnings.append(f"Expected section '{section}' not found in paper")

    if len(present) == len(_STANDARD_SECTIONS):
        passed.append(
            "section_structure_consistency: Abstract, Introduction, Conclusion "
            "and References sections all present"
        )


def _citation_numbers(match: re.Match[str]) -> list[int]:
    """Expand the contents of a [..] citation group into reference numbers."""
    numbers: list[int] = []
    for part in re.split(r"[,\s]+", match.group(1)):
        if not part or not part[0].isdigit():
            continue
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                start, end = int(bounds[0]), int(bounds[1])
                if start <= end:
                    numbers.extend(range(start, end + 1))
        elif part.isdigit():
            numbers.append(int(part))
    return numbers


def _check_reference_continuity(
    full_text: str,
    references: list[ReferenceEntry],
    flags: list[ConsistencyFlag],
    passed: list[str],
) -> None:
    """Rule 5: every reference cited in the text must be in the reference list."""
    defined = {reference.number for reference in references}

    evidence_by_number: dict[int, str] = {}
    cited: set[int] = set()
    for match in _CITATION_RE.finditer(full_text):
        for number in _citation_numbers(match):
            cited.add(number)
            evidence_by_number.setdefault(
                number, _snippet(full_text, match.start(), match.end())
            )

    missing = sorted(cited - defined)
    if missing:
        for number in missing:
            flags.append(
                ConsistencyFlag(
                    rule="reference_number_continuity",
                    severity="medium",
                    message=(
                        f"Reference [{number}] cited in text but not found in reference list"
                    ),
                    evidence=evidence_by_number.get(number, ""),
                )
            )
    else:
        passed.append(
            "reference_number_continuity: every reference cited in text appears "
            "in the reference list"
        )


def check_consistency(
    full_text: str,
    authors: list[str] | None = None,
    references: list[ReferenceEntry] | None = None,
    abstract: str | None = None,
) -> ConsistencyReport:
    """Run all consistency rules over an extracted paper's text.

    `full_text` is the combined extracted text of the paper; `authors` is
    the ordered author list and `references` the structured reference list
    from extraction. Returns an explainable report; no external calls.
    """
    text = full_text or ""
    author_list = authors or []
    reference_list = references or []

    flags: list[ConsistencyFlag] = []
    warnings: list[str] = []
    passed: list[str] = []

    if not text.strip():
        return ConsistencyReport(
            flags=flags,
            warnings=warnings,
            passed_checks=passed,
            consistency_score=1.0,
        )

    _check_date_consistency(text, abstract, reference_list, flags, passed)
    _check_figure_consistency(text, flags, passed)
    _check_author_consistency(text, author_list, flags, passed)
    _check_section_structure(text, warnings, passed)
    _check_reference_continuity(text, reference_list, flags, passed)

    total = len(flags) + len(warnings) + len(passed)
    score = len(passed) / total if total else 1.0
    return ConsistencyReport(
        flags=flags,
        warnings=warnings,
        passed_checks=passed,
        consistency_score=round(score, 4),
    )