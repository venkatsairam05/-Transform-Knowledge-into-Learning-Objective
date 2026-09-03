from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


class DocumentProcessor:
    """Handles extraction of text from various input formats."""

    MAX_INPUT_LENGTH = 50_000

    def process(self, source: str, is_file: bool = False) -> str:
        if is_file:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")

            suffix = path.suffix.lower()
            if suffix == ".pdf":
                return self._extract_pdf(path)
            elif suffix in (".txt", ".md", ".text"):
                return self._extract_text(path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}. Use .pdf, .txt, or .md")

        return self._validate_text(source)

    def _extract_pdf(self, path: Path) -> str:
        if PyPDF2 is None:
            raise ImportError(
                "PyPDF2 is required for PDF processing. "
                "Install it with: pip install PyPDF2"
            )
        text_parts: list[str] = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        text = "\n\n".join(text_parts)
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF.")
        return self._validate_text(text)

    def _extract_text(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        return self._validate_text(text)

    def _validate_text(self, text: str) -> str:
        text = text.strip()
        if not text:
            raise ValueError("Input content is empty.")
        if len(text) > self.MAX_INPUT_LENGTH:
            text = text[: self.MAX_INPUT_LENGTH]
            print(
                f"Warning: Input truncated to {self.MAX_INPUT_LENGTH} characters.",
                file=sys.stderr,
            )
        return text
