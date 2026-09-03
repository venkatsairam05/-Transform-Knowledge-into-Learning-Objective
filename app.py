from __future__ import annotations

import base64
import json
from pathlib import Path

import streamlit as st

from src.llm_service import LLMService
from src.prompt_engineer import PromptEngineer
from src.models import CourseOutput

st.set_page_config(
    page_title="CourseForge AI",
    page_icon="\U0001F393",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROMO_GRADIENTS = [
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
]

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background: linear-gradient(120deg, #1e3c72 0%, #2a5298 100%);
    background-attachment: fixed;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* Animated gradient title */
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #f093fb, #f5576c, #f6d365, #f093fb);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 4s linear infinite;
    margin-bottom: 0.3rem;
}
@keyframes shine {
    0% { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}

.hero-sub {
    color: #e0e7ff;
    font-size: 1.05rem;
    font-weight: 300;
    opacity: 0.9;
}

/* Floating animation container */
.floating-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 18px;
    padding: 24px;
    backdrop-filter: blur(12px);
    animation: floatIn 0.6s ease-out;
}
@keyframes floatIn {
    from { opacity: 0; transform: translateY(24px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Gradient stat cards */
.stat-grid {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin: 18px 0;
}
.stat-card {
    flex: 1 1 140px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 14px;
    padding: 20px 16px;
    color: white;
    text-align: center;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    animation: pulseGlow 3s ease-in-out infinite;
    transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-4px) scale(1.03); }
.stat-card:nth-child(2) { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-card:nth-child(3) { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.stat-card:nth-child(4) { background: linear-gradient(135deg, #fa709a, #fee140); }
.stat-num {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}
.stat-label {
    font-size: 0.8rem;
    opacity: 0.9;
    margin-top: 4px;
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
    50% { box-shadow: 0 8px 34px rgba(240,147,251,0.5); }
}

/* Lesson cards */
.lesson-card {
    background: rgba(255,255,255,0.95);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    border-left: 5px solid #667eea;
    color: #1e293b;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 0.2s;
}
.lesson-card:hover { border-left-color: #f093fb; transform: translateX(4px); }

/* Quiz option buttons */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.6rem 1rem;
    transition: all 0.2s;
    box-shadow: 0 4px 14px rgba(102,126,234,0.4);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(240,147,251,0.5);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(31,41,55,0.98), rgba(55,65,81,0.98)) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] * { color: #e2e8f0; }

/* Chat bubbles */
.chat-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 85%;
    margin-left: auto;
}
.chat-bot {
    background: rgba(255,255,255,0.12);
    color: white;
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 85%;
    border: 1px solid rgba(255,255,255,0.15);
}

/* Flashcard */
.flashcard {
    background: linear-gradient(135deg, #ffecd2, #fcb69f);
    color: #1e293b;
    border-radius: 20px;
    padding: 30px;
    font-size: 1.15rem;
    text-align: center;
    box-shadow: 0 12px 30px rgba(0,0,0,0.3);
    cursor: pointer;
    margin: 10px 0;
    animation: flipIn 0.4s ease-out;
    min-height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
}
@keyframes flipIn {
    from { transform: rotateY(90deg); opacity: 0; }
    to { transform: rotateY(0); opacity: 1; }
}

.feedback-correct {
    color: #86efac;
    font-weight: 600;
}
.feedback-wrong {
    color: #fca5a5;
    font-weight: 600;
}

/* Progress bar glow */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #f093fb, #f5576c, #f6d365);
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 100px;
    padding: 10px 24px;
    font-weight: 600;
    color: white;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #f093fb, #f5576c);
}

/* Loading spinner styling */
.stSpinner > div { border-top-color: #f093fb !important; }

/* Animating background particles */
@keyframes floaty {
    0% { transform: translateY(0) translateX(0); opacity: 0.3; }
    50% { transform: translateY(-40px) translateX(20px); opacity: 0.8; }
    100% { transform: translateY(0) translateX(0); opacity: 0.3; }
}

h1, h2, h3 { color: white; }
p, li { color: #e2e8f0; }
</style>
"""


def init_state():
    defaults = {
        "course_result": None,
        "course_json": None,
        "chat_history": [],
        "flashcard_index": 0,
        "flashcard_flipped": False,
        "quiz_attempts": {},
        "quiz_score": 0,
        "quiz_total": 0,
        "topic_focus": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar() -> tuple:
    with st.sidebar:
        st.markdown("<h3 style='margin-top:0'>\U00002699\ufe0f Settings</h3>", unsafe_allow_html=True)
        api_key = st.text_input(
            "OpenAI API Key", type="password", placeholder="sk-...",
            help="Get at platform.openai.com/api-keys",
        )
        model = st.selectbox(
            "Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0,
        )
        temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)
        st.divider()
        st.markdown("<b>How it works</b>")
        st.markdown(
            "1\ufe0f\u20e3 Enter a topic or upload a doc\n\n"
            "2\ufe0f\u20e3 Generate your course\n\n"
            "3\ufe0f\u20e3 Explore lessons, quizzes, flashcards\n\n"
            "4\ufe0f\u20e3 Ask any question about the course"
        )
        if not api_key:
            st.warning("Add your API key to activate.")
    return api_key, model, temperature


def extract_text(uploaded) -> str:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".pdf":
        import PyPDF2
        reader = PyPDF2.PdfReader(uploaded)
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    return uploaded.read().decode("utf-8")


def generate_course(content, api_key, model, temperature):
    llm = LLMService(api_key=api_key, model=model, temperature=temperature, max_retries=3)
    raw = llm.generate_course(content)
    return raw, CourseOutput.from_dict(raw).to_dict()


def stat_cards(course):
    cols = st.columns(4)
    data = [
        ("\U0001f4dd", len(course["learningObjectives"]), "Objectives"),
        ("\U0001f4d6", len(course["lessonOutline"]), "Lessons"),
        ("\U00002753", len(course["quizQuestions"]), "Quiz Q's"),
        ("\U0001f4ac", len(course["lessonSummaries"]), "Summaries"),
    ]
    for col, (icon, num, label) in zip(cols, data):
        col.markdown(
            f"""
            <div class="stat-card">
                <div>{icon}</div>
                <div class="stat-num">{num}</div>
                <div class="stat-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_overview(course):
    st.markdown("<div class='floating-card'>", unsafe_allow_html=True)
    st.subheader("\U0001f3af Learning Objectives")
    for obj in course["learningObjectives"]:
        st.markdown(f"\u2705 {obj}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='floating-card'>", unsafe_allow_html=True)
    st.subheader("\U0001f4cf Lesson Outline")
    for i, lesson in enumerate(course["lessonOutline"], 1):
        grad = PROMO_GRADIENTS[i % len(PROMO_GRADIENTS)]
        st.markdown(
            f"<div class='lesson-card' style='border-left-color:#667eea'>{lesson}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_lessons(course):
    st.subheader("\U0001f4d6 Lesson Summaries")
    for i, summary in enumerate(course["lessonSummaries"], 1):
        title = course["lessonOutline"][i - 1] if i <= len(course["lessonOutline"]) else f"Lesson {i}"
        with st.expander(f"\U0001f4c5 {i}. {title}", expanded=(i == 1)):
            st.markdown(summary)


def render_quiz(course, api_key, model, temperature):
    st.subheader("\U00002753 Interactive Quiz")
    total_qs = len(course["quizQuestions"])
    answered = sum(1 for q in course["quizQuestions"] if st.session_state.quiz_attempts.get(f"q{q['question']}"))
    score = sum(
        1 for q in course["quizQuestions"]
        if st.session_state.quiz_attempts.get(f"q{q['question']}") is not None
        and st.session_state.quiz_attempts.get(f"q{q['question']}") == q["correctAnswerIndex"]
    )

    st.markdown(
        f"<div style='color:white;margin-bottom:8px'>Score: "
        f"<b style='color:#86efac'>{score}/{answered}</b></div>",
        unsafe_allow_html=True,
    )
    st.progress(answered / total_qs if total_qs else 0)

    for i, q in enumerate(course["quizQuestions"], 1):
        st.markdown(f"<div class='lesson-card'><b>Q{i}:</b> {q['question']}</div>", unsafe_allow_html=True)
        key = f"q{q['question']}"
        selected = st.radio(
            "Choose:", range(4), index=None,
            format_func=lambda x, qq=q: f"{chr(65 + x)}) {qq['options'][x]}",
            key=f"radio_{key}",
            label_visibility="collapsed",
        )
        col_footer = st.columns([1, 1])
        if col_footer[0].button(f"Submit Q{i}", key=f"submit_{key}"):
            if selected is not None:
                st.session_state.quiz_attempts[key] = selected
                st.rerun()
            else:
                st.warning("Select an answer first.")

        if key in st.session_state.quiz_attempts:
            chosen = st.session_state.quiz_attempts[key]
            correct = q["correctAnswerIndex"]
            if chosen == correct:
                st.markdown(f"<div class='feedback-correct'>\u2714 Correct!</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='feedback-wrong'>\u2716 Incorrect. Correct answer: "
                    f"{chr(65 + correct)}) {q['options'][correct]}</div>",
                    unsafe_allow_html=True,
                )
            if q.get("explanation"):
                st.info(q["explanation"])
        st.markdown("<br>", unsafe_allow_html=True)

    if answered == total_qs and total_qs:
        pct = score / total_qs
        if pct == 1.0:
            st.balloons()
            st.success("Perfect score! \U0001f389 Mastery achieved!")
        elif pct >= 0.7:
            st.success("Great job! Keep practicing.")
        else:
            st.info("Review the lessons and try again.")


def render_flashcards(course):
    st.subheader("\U0001f4a1 Flashcards")
    items = []
    for i, title in enumerate(course["lessonOutline"]):
        summary = course["lessonSummaries"][i] if i < len(course["lessonSummaries"]) else ""
        items.append(("Lesson", title, summary))
    for i, q in enumerate(course["quizQuestions"]):
        items.append(("Question", q["question"], f"{chr(65 + q['correctAnswerIndex'])}) {q['options'][q['correctAnswerIndex']]}"))

    if not items:
        st.info("No flashcards available.")
        return

    idx = st.session_state.flashcard_index % len(items)
    ftype, front, back = items[idx]

    st.markdown(
        f"<div class='flashcard'>{'<b>' + ftype + '</b><br>' if ftype else ''}{front}</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    if c1.button("\U00002b05 Prev"):
        st.session_state.flashcard_index = (idx - 1) % len(items)
        st.rerun()
    if c2.button("\U0001f441 Reveal"):
        st.info(back)
    if c3.button("\U000027a1 Next"):
        st.session_state.flashcard_index = (idx + 1) % len(items)
        st.rerun()

    st.caption(f"Card {idx + 1} of {len(items)}")


def render_ask(course, api_key, model, temperature):
    st.subheader("\U0001f4ac Ask About the Course")
    st.markdown(
        "<span style='color:#e2e8f0'>Ask any question and get an <b>accurate</b> answer grounded in "
        "the course material.</span>",
        unsafe_allow_html=True,
    )

    content_section = "\n\n".join(course["lessonSummaries"])
    question = st.chat_input("Ask a question about " + course["courseTitle"] + "...")

    if question and api_key:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.spinner("Thinking..."):
            try:
                llm = LLMService(api_key=api_key, model=model, temperature=temperature)
                answer = llm.answer_question(course["courseTitle"], content_section, question)
                st.session_state.chat_history.append({"role": "bot", "content": answer})
            except Exception as e:
                st.session_state.chat_history.append({"role": "bot", "content": f"Error: {e}"})
        st.rerun()

    for msg in st.session_state.chat_history:
        cls = "chat-user" if msg["role"] == "user" else "chat-bot"
        align = "left" if msg["role"] == "bot" else "right"
        st.markdown(
            f"<div class='{cls}' style='text-align:{align}'>{msg['content']}</div>",
            unsafe_allow_html=True,
        )


def main():
    init_state()
    api_key, model, temperature = render_sidebar()

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-title'>\U0001f393 CourseForge AI</div>"
        "<div class='hero-sub'>Transform any knowledge into a stunning, interactive learning course "
        "with quizzes, flashcards & an AI tutor.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:rgba(255,255,255,0.2)'>", unsafe_allow_html=True)

    tab_gen, tab_course, tab_quiz, tab_flash, tab_ask = st.tabs(
        ["\u2728 Generate", "\U0001f4d6 Course", "\U00002753 Quiz", "\U0001f4a1 Flashcards", "\U0001f4ac Ask Tutor"]
    )

    course_result = st.session_state.course_result

    with tab_gen:
        st.markdown("<div class='floating-card'>", unsafe_allow_html=True)
        st.subheader("\U0001f4e4 Input")
        mode = st.radio("Input type:", ["Text Prompt", "Upload Document"], horizontal=True)

        topic = st.text_input("Focus topic (optional)", placeholder="e.g., Quantum Mechanics", key="focus_input")
        content = None
        if mode == "Text Prompt":
            content = st.text_area(
                "Enter your topic or content:", height=160,
                placeholder="Paste or describe the knowledge you want to turn into a course...",
            )
        else:
            up = st.file_uploader("Upload (PDF/TXT/MD)", type=["pdf", "txt", "md"])
            if up:
                try:
                    content = extract_text(up)
                    with st.expander("Preview"):
                        st.text_area("Extracted", content[:1500], height=160, disabled=True)
                except Exception as e:
                    st.error(f"Read error: {e}")

        do_gen = st.button("\U0001f680 Generate Course", type="primary", use_container_width=True,
                           disabled=not (content and api_key))

        if do_gen and content and api_key:
            with st.spinner("Crafting your course... this may take 15-30s \u23f3"):
                try:
                    raw, result = generate_course(content, api_key, model, temperature)
                    st.session_state.course_result = result
                    st.session_state.course_json = json.dumps(result, indent=2, ensure_ascii=False)
                    st.session_state.chat_history = []
                    st.session_state.quiz_attempts = {}
                    st.balloons()
                    st.success("Course generated! Explore the tabs above. \U0001f389")
                except Exception as e:
                    st.error(f"Generation failed: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        if course_result:
            st.markdown("## \U0001f4ca Generated Course Overview")
            st.markdown(f"<h2 style='color:#f093fb'>{course_result['courseTitle']}</h2>", unsafe_allow_html=True)
            stat_cards(course_result)

    with tab_course:
        if course_result:
            render_overview(course_result)
            render_lessons(course_result)
        else:
            st.info("No course yet. Generate one in the \u2728 Generate tab.")

    with tab_quiz:
        if course_result:
            render_quiz(course_result, api_key, model, temperature)
        else:
            st.info("No course yet. Generate one in the \u2728 Generate tab.")

    with tab_flash:
        if course_result:
            render_flashcards(course_result)
        else:
            st.info("No course yet. Generate one in the \u2728 Generate tab.")

    with tab_ask:
        if course_result:
            render_ask(course_result, api_key, model, temperature)
        else:
            st.info("No course yet. Generate one in the \u2728 Generate tab.")


if __name__ == "__main__":
    main()
