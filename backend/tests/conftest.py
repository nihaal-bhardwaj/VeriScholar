"""Shared test fixtures and PDF generators."""

import io

import fitz
import pytest

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient bound to the application."""
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


def build_pdf(text: str, pages: list[str] | None = None) -> bytes:
    """Create an in-memory PDF containing the given text using PyMuPDF.

    Uses insert_textbox so long lines wrap instead of being clipped.
    """
    buffer = io.BytesIO()
    document = fitz.open()
    for page_text in pages or [text]:
        page = document.new_page()
        rect = page.rect + (36, 36, -36, -36)
        page.insert_textbox(rect, page_text, fontsize=11, align=0)
    document.save(buffer)
    document.close()
    return buffer.getvalue()


SAMPLE_PAPER_PAGE_1 = (
    "Deep Learning for Iceberg Detection\n"
    "Abstract\n"
    "We study convolutional models for iceberg detection in radar imagery. "
    "Our method reaches 94% accuracy. https://doi.org/10.1234/example.2026\n"
    "Keywords: iceberg, radar, deep learning\n"
    "1. Introduction\n"
    "Icebergs threaten navigation.\n"
)

SAMPLE_PAPER_PAGE_2 = (
    "2. Method\n"
    "We use a ResNet backbone.\n"
    "References\n"
    "[1] A. Author, Iceberg Radar Survey, Journal of Polar Research, 2024.\n"
    "[2] B. Author, https://doi.org/10.5678/iceberg.v2 Deep Learning in Remote Sensing, 2025.\n"
)
