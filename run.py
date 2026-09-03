#!/usr/bin/env python3
"""
run.py - Standalone execution script for the Knowledge-to-Course generator.

This script demonstrates the full pipeline:
1. Prompt/template construction
2. LLM API integration
3. Structured output extraction and validation
4. JSON serialization

Usage:
    python run.py --prompt "Introduction to Quantum Mechanics"
    python run.py --file input/sample.txt
    python run.py --prompt "Machine Learning basics" --model gpt-4o-mini
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from src.document_processor import DocumentProcessor
from src.llm_service import LLMService
from src.models import CourseOutput


def run_pipeline(content_source: str, is_file: bool, model: str, temperature: float) -> dict:
    """Execute the full course generation pipeline."""

    doc_processor = DocumentProcessor()
    print("[1/4] Processing input...")
    content = doc_processor.process(content_source, is_file=is_file)
    print(f"  -> Extracted {len(content)} characters of content.")

    llm_service = LLMService(api_key=os.environ["OPENAI_API_KEY"], model=model, temperature=temperature)
    print(f"[2/4] Calling LLM API (model={model})...")
    raw_response = llm_service.generate_course(content)
    print(f"  -> Received structured response with {len(raw_response.get('quizQuestions', []))} quiz questions.")

    print("[3/4] Validating and parsing output...")
    course = CourseOutput.from_dict(raw_response)

    print("[4/4] Done.")
    return course.to_dict()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate a learning course from knowledge content.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", "-p", help="Text prompt describing the topic")
    source.add_argument("--file", "-f", help="Path to input file (.pdf, .txt, .md)")
    parser.add_argument("--model", "-m", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Temperature (default: 0.7)")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path")

    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: Set OPENAI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    is_file = args.file is not None
    source = args.file if is_file else args.prompt

    try:
        result = run_pipeline(source, is_file, args.model, args.temperature)

        output_path = args.output
        if not output_path:
            output_path = f"output/course_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nOutput saved to: {output_path}")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
