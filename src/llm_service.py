from __future__ import annotations

import json
import sys
import time
from typing import Optional

from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError

from .prompt_engineer import PromptEngineer


class LLMService:
    """Manages communication with the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_retries: int = 3,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.prompt_engineer = PromptEngineer()

    def generate_course(self, content: str) -> dict:
        messages = self.prompt_engineer.build_messages(content)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or ""
                parsed = self.prompt_engineer.parse_response(raw)
                self._validate_schema(parsed)
                return parsed

            except (RateLimitError, APIConnectionError) as e:
                last_error = e
                wait = 2 ** attempt
                print(
                    f"Attempt {attempt}/{self.max_retries} failed ({type(e).__name__}). "
                    f"Retrying in {wait}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)

            except APIStatusError as e:
                last_error = e
                if e.status_code >= 500:
                    wait = 2 ** attempt
                    print(
                        f"Attempt {attempt}/{self.max_retries} failed (server error {e.status_code}). "
                        f"Retrying in {wait}s...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"API error {e.status_code}: {e.message}") from e

            except json.JSONDecodeError as e:
                last_error = e
                print(
                    f"Attempt {attempt}/{self.max_retries} failed (invalid JSON). Retrying...",
                    file=sys.stderr,
                )

            except ValueError as e:
                last_error = e
                print(
                    f"Attempt {attempt}/{self.max_retries} failed (validation: {e}). Retrying...",
                    file=sys.stderr,
                )

        raise RuntimeError(
            f"Failed after {self.max_retries} attempts. Last error: {last_error}"
        )

    @staticmethod
    def _validate_schema(data: dict) -> None:
        required = [
            "courseTitle",
            "learningObjectives",
            "lessonOutline",
            "quizQuestions",
            "lessonSummaries",
        ]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        if not isinstance(data["quizQuestions"], list) or len(data["quizQuestions"]) != 5:
            raise ValueError("quizQuestions must be an array of exactly 5 questions.")

        for i, q in enumerate(data["quizQuestions"]):
            if "question" not in q or "options" not in q or "correctAnswerIndex" not in q:
                raise ValueError(f"Quiz question {i} is missing required fields.")
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                raise ValueError(f"Quiz question {i} must have exactly 4 options.")
            if not (0 <= q["correctAnswerIndex"] <= 3):
                raise ValueError(f"Quiz question {i} correctAnswerIndex must be 0-3.")
