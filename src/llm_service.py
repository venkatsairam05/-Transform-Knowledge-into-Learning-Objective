from __future__ import annotations

import json
import sys
import time
from typing import Optional

from .prompt_engineer import PromptEngineer


class LLMClient:
    """Base class for LLM providers. Subclasses implement the API calls."""

    def __init__(self, model: str, temperature: float, max_retries: int = 3):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.prompt_engineer = PromptEngineer()

    # ---- subclass hooks ----
    def _complete(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        raise NotImplementedError

    # ---- shared logic ----
    def generate_course(self, content: str) -> dict:
        messages = self.prompt_engineer.build_messages(content)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._complete(messages, self.temperature, 4096)
                parsed = self.prompt_engineer.parse_response(raw)
                self._validate_schema(parsed)
                return parsed

            except (RateLimit, APIConnection, ServerError) as e:
                last_error = e
                wait = 2 ** attempt
                print(
                    f"Attempt {attempt}/{self.max_retries} failed ({type(e).__name__}). "
                    f"Retrying in {wait}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)

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

    def answer_question(
        self, course_title: str, content_section: str, question: str
    ) -> str:
        messages = self.prompt_engineer.build_answer_messages(
            course_title, content_section, question
        )

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._complete(messages, 0.3, 1024)
                return self.prompt_engineer.parse_answer(raw)

            except (RateLimit, APIConnection, ServerError) as e:
                last_error = e
                wait = 2 ** attempt
                print(
                    f"Attempt {attempt}/{self.max_retries} failed ({type(e).__name__}). "
                    f"Retrying in {wait}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)

            except Exception as e:
                last_error = e
                print(
                    f"Attempt {attempt}/{self.max_retries} failed. Retrying...",
                    file=sys.stderr,
                )

        raise RuntimeError(
            f"Failed to answer question after {self.max_retries} attempts. Last error: {last_error}"
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


# ---- Error wrappers (normalized across providers) ----
class RateLimit(Exception):
    pass


class APIConnection(Exception):
    pass


class ServerError(Exception):
    pass


class OpenAIProvider(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7, max_retries: int = 3):
        super().__init__(model, temperature, max_retries)
        from openai import OpenAI, APIConnectionError as _Conn, APIStatusError as _Status, RateLimitError as _Rate
        self._client = OpenAI(api_key=api_key)
        self._err = (_Conn, _Status, _Rate)

    def _complete(self, messages, temperature, max_tokens) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except self._err[2] as e:  # RateLimitError
            raise RateLimit(str(e)) from e
        except self._err[0] as e:  # APIConnectionError
            raise APIConnection(str(e)) from e
        except self._err[1] as e:  # APIStatusError
            if e.status_code >= 500:
                raise ServerError(str(e)) from e
            raise RuntimeError(f"API error {e.status_code}: {e.message}") from e


class GeminiProvider(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash", temperature: float = 0.7, max_retries: int = 3):
        super().__init__(model, temperature, max_retries)
        from google import genai
        from google.genai import types
        self._client = genai.Client(api_key=api_key)
        self._types = types

    def _complete(self, messages, temperature, max_tokens) -> str:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user = "\n\n".join(m["content"] for m in messages if m["role"] == "user")

        config = self._types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system,
            response_mime_type="application/json",
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg:
                raise RateLimit(str(e)) from e
            if "permission" in msg or "api key" in msg or "403" in msg:
                raise RuntimeError(f"Gemini auth/API error: {e}") from e
            if "500" in msg or "503" in msg:
                raise ServerError(str(e)) from e
            raise e


def create_llm(
    provider: str = "openai",
    api_key: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_retries: int = 3,
) -> LLMClient:
    """Factory: returns an OpenAI or Gemini client based on provider name."""
    provider = (provider or "openai").lower()

    if provider == "gemini":
        if model == "gpt-4o" or not model:
            model = "gemini-3.6-flash"
        return GeminiProvider(api_key=api_key, model=model, temperature=temperature, max_retries=max_retries)

    # default: openai
    return OpenAIProvider(api_key=api_key, model=model, temperature=temperature, max_retries=max_retries)


class LLMService:
    """Backwards-compatible wrapper matching the old constructor signature.

    provider can be 'openai' or 'gemini'. For gemini, pass a Gemini API key
    and optionally a gemini model name.
    """

    def __new__(
        cls,
        api_key: str = "",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_retries: int = 3,
        provider: str = "openai",
    ):
        return create_llm(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
        )


def get_llm(
    provider: str = "openai",
    api_key: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
) -> LLMClient:
    return create_llm(provider=provider, api_key=api_key, model=model, temperature=temperature)
