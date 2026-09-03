from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correctAnswerIndex: int
    explanation: Optional[str] = None


@dataclass
class CourseOutput:
    courseTitle: str
    learningObjectives: List[str]
    lessonOutline: List[str]
    quizQuestions: List[QuizQuestion]
    lessonSummaries: List[str]

    def to_dict(self) -> dict:
        return {
            "courseTitle": self.courseTitle,
            "learningObjectives": self.learningObjectives,
            "lessonOutline": self.lessonOutline,
            "quizQuestions": [
                {
                    "question": q.question,
                    "options": q.options,
                    "correctAnswerIndex": q.correctAnswerIndex,
                    **({"explanation": q.explanation} if q.explanation else {}),
                }
                for q in self.quizQuestions
            ],
            "lessonSummaries": self.lessonSummaries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CourseOutput":
        quiz_questions = [
            QuizQuestion(
                question=q["question"],
                options=q["options"],
                correctAnswerIndex=q["correctAnswerIndex"],
                explanation=q.get("explanation"),
            )
            for q in data.get("quizQuestions", [])
        ]
        return cls(
            courseTitle=data["courseTitle"],
            learningObjectives=data["learningObjectives"],
            lessonOutline=data["lessonOutline"],
            quizQuestions=quiz_questions,
            lessonSummaries=data["lessonSummaries"],
        )
