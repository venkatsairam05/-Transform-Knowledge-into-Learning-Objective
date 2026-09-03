"""
web_app.py - Flask web application for the Knowledge-to-Course generator.

Serves a self-contained HTML/CSS/JS frontend over plain HTTP (no WebSocket),
so it renders reliably in any browser. Uses the same backend modules as the
CLI for document processing and LLM integration.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402

from src.document_processor import DocumentProcessor  # noqa: E402
from src.llm_service import LLMService  # noqa: E402
from src.models import CourseOutput  # noqa: E402

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), template_folder=str(BASE_DIR / "templates"))


def resolve_key(provider: str, api_key: str) -> str:
    api_key = (api_key or "").strip()
    if api_key:
        return api_key
    env_var = "GEMINI_API_KEY" if (provider or "").lower() == "gemini" else "OPENAI_API_KEY"
    return os.environ.get(env_var, "")


def get_llm(provider: str, api_key: str | None = None, model: str = "") -> object:
    key = resolve_key(provider, api_key or "")
    provider_model = {
        "gemini": "gemini-2.0-flash",
        "openai": "gpt-4o",
    }.get((provider or "openai").lower(), "gpt-4o")
    if not model:
        model = provider_model
    if not key:
        friendly = "GEMINI_API_KEY" if (provider or "").lower() == "gemini" else "OPENAI_API_KEY"
        raise RuntimeError(
            f"No {friendly} found. Either set it in the .env file, "
            "or paste your API key in the input field on the page."
        )
    return LLMService(
        api_key=key,
        model=model,
        temperature=0.7,
        max_retries=2,
        provider=(provider or "openai").lower(),
    )


@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR / "templates"), "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(BASE_DIR / "static"), filename)


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        payload = request.get_json(silent=True) or {}
        content = (payload.get("content") or "").strip()
        api_key = (payload.get("apiKey") or "").strip()
        provider = (payload.get("provider") or "openai").lower()
        model = (payload.get("model") or "").strip()
        if not content:
            return jsonify({"error": "Please enter some content first."}), 400
        if len(content) > 50000:
            content = content[:50000]

        valid = DocumentProcessor().process(content, is_file=False)
        llm = get_llm(provider, api_key, model)
        raw = llm.generate_course(valid)
        course = CourseOutput.from_dict(raw).to_dict()
        return jsonify({"course": course}), 200

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded."}), 400
        suffix = Path(file.filename or "").suffix.lower()
        if suffix == ".pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            content = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        else:
            try:
                content = file.read().decode("utf-8")
            except UnicodeDecodeError:
                content = file.read().decode("latin-1")
        if not content.strip():
            return jsonify({"error": "No text could be extracted."}), 400
        return jsonify({"content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def api_ask():
    try:
        payload = request.get_json(silent=True) or {}
        question = (payload.get("question") or "").strip()
        course = payload.get("course") or {}
        api_key = (payload.get("apiKey") or "").strip()
        provider = (payload.get("provider") or "openai").lower()
        model = (payload.get("model") or "").strip()
        if not question:
            return jsonify({"error": "Please enter a question."}), 400
        title = course.get("courseTitle", "the course")
        section = "\n\n".join(course.get("lessonSummaries", []))
        llm = get_llm(provider, api_key, model)
        answer = llm.answer_question(title, section, question)
        return jsonify({"answer": answer}), 200
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error answering: {e}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"CourseForge AI running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
