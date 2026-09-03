from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .course_generator import CourseGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transform knowledge from documents or text prompts into structured learning courses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Generate course from a text prompt
  python -m src.main --prompt "Introduction to Python programming"

  # Generate course from a PDF file
  python -m src.main --file input/quantum_mechanics.pdf

  # Generate with custom output path and model
  python -m src.main --prompt "Machine Learning basics" --output output/ml_course.json --model gpt-4o-mini
        """,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", "-p", help="Text prompt describing the topic")
    source.add_argument("--file", "-f", help="Path to input file (.pdf, .txt, .md)")

    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: output/course_<timestamp>.json)",
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Generation temperature (default: 0.7)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )
    return parser


def main() -> int:
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Set it with: export OPENAI_API_KEY=your-key-here", file=sys.stderr)
        return 1

    output_path = args.output
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/course_{timestamp}.json"

    try:
        generator = CourseGenerator(
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
        )

        print(f"Generating course using model: {args.model}")

        if args.prompt:
            print(f"Source: Text prompt")
            course = generator.generate_from_text(args.prompt)
        else:
            print(f"Source: File - {args.file}")
            course = generator.generate_from_file(args.file)

        saved = generator.save_output(course, output_path)
        print(f"\nCourse generated successfully!")
        print(f"Title: {course.courseTitle}")
        print(f"Lessons: {len(course.lessonOutline)}")
        print(f"Quiz Questions: {len(course.quizQuestions)}")
        print(f"Output saved to: {saved}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Runtime Error: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
