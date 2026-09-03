from __future__ import annotations

import json

SYSTEM_PROMPT = """\
You are an expert instructional designer and course creator. \
Your task is to transform the provided knowledge content into a structured learning course.

You must respond with a single valid JSON object matching the schema below. \
Do NOT include any text outside the JSON object. No markdown fences, no commentary.

Schema:
{
  "courseTitle": "string - A clear, descriptive course title",
  "learningObjectives": ["string - 3-5 specific, measurable learning objectives"],
  "lessonOutline": ["string - Numbered lesson titles, e.g. '1. Lesson Title'"],
  "quizQuestions": [
    {
      "question": "string - A clear question testing understanding",
      "options": ["string A", "string B", "string C", "string D"],
      "correctAnswerIndex": 0,
      "explanation": "string - Brief explanation of the correct answer"
    }
  ],
  "lessonSummaries": ["string - One concise summary paragraph per lesson in lessonOutline"]
}

Guidelines:
- Generate exactly 5 quiz questions with 4 options each (A-D).
- Ensure quiz questions cover different lessons/topics.
- Learning objectives should use action verbs (understand, analyze, apply, etc.).
- Lesson summaries should be 2-4 sentences each.
- All arrays must have consistent lengths where they correspond to each other.
- The correctAnswerIndex must be 0-3.
"""

USER_PROMPT_TEMPLATE = """\
Transform the following content into a structured learning course:

---
{content}
---

Respond with ONLY the JSON object. No extra text."""


class PromptEngineer:
    """Constructs prompts for the LLM to generate course content."""

    def build_messages(self, content: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(content=content)},
        ]

    @staticmethod
    def parse_response(raw: str) -> dict:
        text = raw.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response.")
        text = text[start : end + 1]

        return json.loads(text)
