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


GEMINI_FALLBACK_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
)


class GeminiProvider(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash", temperature: float = 0.7, max_retries: int = 3):
        super().__init__(model, temperature, max_retries)
        from google import genai
        from google.genai import types
        self._client = genai.Client(api_key=api_key)
        self._types = types
        candidates = [model] + [m for m in GEMINI_FALLBACK_MODELS if m != model]
        self._models = [m for m in candidates if m]
        self._model_index = 0

    def _active_model(self) -> str:
        return self._models[self._model_index]

    def _advance_model(self) -> bool:
        if self._model_index < len(self._models) - 1:
            self._model_index += 1
            self.model = self._models[self._model_index]
            return True
        return False

    def _complete(self, messages, temperature, max_tokens) -> str:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user = "\n\n".join(m["content"] for m in messages if m["role"] == "user")

        config = self._types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system,
            response_mime_type="application/json",
        )

        last_error: Optional[Exception] = None
        for _ in range(len(self._models)):
            active = self._active_model()
            try:
                response = self._client.models.generate_content(
                    model=active,
                    contents=user,
                    config=config,
                )
                if not response.text:
                    raise ServerError(f"Empty response from {active}")
                return response.text

            except Exception as e:
                msg = str(e).lower()
                if "quota" in msg or "rate" in msg or "429" in msg:
                    last_error = RateLimit(str(e))
                elif "permission" in msg or "api key" in msg or "403" in msg:
                    raise RuntimeError(f"Gemini auth/API error: {e}") from e
                elif any(code in msg for code in ("500", "502", "503", "504", "404", "not_found", "unavailable")):
                    last_error = ServerError(str(e))
                else:
                    raise e

                if not self._advance_model():
                    raise last_error from e

        raise last_error if last_error else ServerError("Gemini request failed")


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
