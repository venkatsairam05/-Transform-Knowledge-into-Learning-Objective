from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from src.document_processor import DocumentProcessor
from src.llm_service import LLMService
from src.models import CourseOutput


st.set_page_config(
    page_title="Knowledge to Course Generator",
    page_icon="\U0001F393",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
    }
    .quiz-card {
        background: #f8f9fa;
        border-left: 4px solid #4A90D9;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .quiz-card h4 { margin-top: 0; color: #4A90D9; }
    .option-correct { color: #28a745; font-weight: bold; }
    .option-wrong { color: #dc3545; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    defaults = {
        "course_result": None,
        "course_json": None,
        "generating": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    with st.sidebar:
        st.header("Settings")

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Required. Get yours at platform.openai.com/api-keys",
        )

        model = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Lower = more focused, Higher = more creative",
        )

        st.divider()
        st.markdown(
            "**How it works**\n"
            "1. Enter a topic or upload a document\n"
            "2. Click **Generate Course**\n"
            "3. View your structured course with quizzes\n"
            "4. Download the JSON output"
        )

    return api_key, model, temperature


def extract_text_from_upload(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".pdf":
        import PyPDF2

        reader = PyPDF2.PdfReader(uploaded_file)
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts)

    elif suffix in (".txt", ".md", ".text"):
        return uploaded_file.read().decode("utf-8")

    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def generate_course(content: str, api_key: str, model: str, temperature: float) -> dict:
    llm = LLMService(api_key=api_key, model=model, temperature=temperature)
    raw = llm.generate_course(content)
    return CourseOutput.from_dict(raw).to_dict()


def display_course(course: dict):
    st.subheader(course["courseTitle"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Learning Objectives")
        for obj in course["learningObjectives"]:
            st.markdown(f"- {obj}")

    with col2:
        st.markdown("### Lesson Outline")
        for lesson in course["lessonOutline"]:
            st.markdown(f"- {lesson}")

    st.divider()

    st.markdown("### Lesson Summaries")
    for i, summary in enumerate(course["lessonSummaries"], 1):
        lesson_title = course["lessonOutline"][i - 1] if i <= len(course["lessonOutline"]) else f"Lesson {i}"
        with st.expander(lesson_title, expanded=(i == 1)):
            st.markdown(summary)

    st.divider()

    st.markdown("### Quiz")
    for i, q in enumerate(course["quizQuestions"], 1):
        with st.container():
            st.markdown(f"**Question {i}:** {q['question']}")
            cols = st.columns([1, 3])
            with cols[0]:
                selected = st.radio(
                    "Your answer",
                    options=range(4),
                    format_func=lambda x, idx=i: f"{chr(65 + x)})",
                    key=f"quiz_{i}",
                    label_visibility="collapsed",
                )
            with cols[1]:
                correct = q["correctAnswerIndex"]
                labels = [
                    f"{'✅ ' if j == correct else ''}{chr(65 + j)}) {opt}"
                    for j, opt in enumerate(q["options"])
                ]
                st.markdown("**Options:**")
                for j, label in enumerate(labels):
                    if j == correct:
                        st.markdown(f"<span class='option-correct'>{label}</span>", unsafe_allow_html=True)
                    elif j == selected and j != correct:
                        st.markdown(f"<span class='option-wrong'>{label}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"  {label}")

            if q.get("explanation"):
                st.info(f"**Explanation:** {q['explanation']}")
            st.markdown("---")


def main():
    init_session_state()
    api_key, model, temperature = render_sidebar()

    st.title("Knowledge to Course Generator")
    st.markdown("Transform any knowledge into a structured learning course with quizzes using AI.")

    tab_input, tab_output = st.tabs(["Input", "Output"])

    with tab_input:
        input_mode = st.radio(
            "Choose input method:",
            ["Text Prompt", "Upload Document"],
            horizontal=True,
        )

        content = None

        if input_mode == "Text Prompt":
            content = st.text_area(
                "Enter your topic or content:",
                height=200,
                placeholder="e.g., Introduction to Quantum Mechanics, Machine Learning basics...",
            )
        else:
            uploaded = st.file_uploader(
                "Upload a document",
                type=["pdf", "txt", "md"],
                help="Supported: PDF, TXT, Markdown",
            )
            if uploaded:
                try:
                    content = extract_text_from_upload(uploaded)
                    with st.expander("Preview extracted text", expanded=False):
                        st.text_area("Extracted content", value=content[:2000], height=200, disabled=True)
                        if len(content) > 2000:
                            st.caption(f"... ({len(content)} total characters)")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        st.markdown("")
        generate_clicked = st.button(
            "Generate Course",
            type="primary",
            use_container_width=True,
            disabled=(not content or not api_key),
        )

        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar to continue.")

        if generate_clicked and content and api_key:
            st.session_state.generating = True
            with st.spinner("Generating course... This may take 15-30 seconds."):
                try:
                    result = generate_course(content, api_key, model, temperature)
                    st.session_state.course_result = result
                    st.session_state.course_json = json.dumps(result, indent=2, ensure_ascii=False)
                    st.session_state.generating = False
                    st.success("Course generated!")
                    st.rerun()
                except Exception as e:
                    st.session_state.generating = False
                    st.error(f"Generation failed: {e}")

    with tab_output:
        result = st.session_state.course_result
        if result:
            display_course(result)

            st.divider()
            st.download_button(
                "Download JSON",
                data=st.session_state.course_json,
                file_name="course_output.json",
                mime="application/json",
                use_container_width=True,
            )

            with st.expander("Raw JSON Output", expanded=False):
                st.code(st.session_state.course_json, language="json")
        else:
            st.info("Generate a course from the Input tab to see results here.")


if __name__ == "__main__":
    main()
