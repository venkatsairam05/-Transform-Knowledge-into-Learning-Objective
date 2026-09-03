from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .document_processor import DocumentProcessor
from .llm_service import LLMService
from .models import CourseOutput


class CourseGenerator:
    """Orchestrates the full pipeline: input -> LLM -> validated output."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        provider: str = "openai",
    ):
        self.doc_processor = DocumentProcessor()
        self.llm_service = LLMService(
            api_key=api_key,
            model=model,
            temperature=temperature,
            provider=provider,
        )

    def generate_from_text(self, text: str) -> CourseOutput:
        content = self.doc_processor.process(text, is_file=False)
        raw = self.llm_service.generate_course(content)
        return CourseOutput.from_dict(raw)

    def generate_from_file(self, filepath: str) -> CourseOutput:
        content = self.doc_processor.process(filepath, is_file=True)
        raw = self.llm_service.generate_course(content)
        return CourseOutput.from_dict(raw)

    @staticmethod
    def save_output(course: CourseOutput, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(course.to_dict(), f, indent=2, ensure_ascii=False)
        return path
