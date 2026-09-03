from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.llm_service import LLMService
from src.models import CourseOutput

st.set_page_config(
    page_title="CourseForge AI",
    page_icon="\U0001f393",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* ===== Full dark animated background ===== */
.stApp {
    background: radial-gradient(ellipse at top left, #0f0c29 0%, #302b63 40%, #24243e 100%);
    position: relative;
    overflow-x: hidden;
}

/* Animated floating orbs */
.stApp::before,
.stApp::after {
    content: '';
    position: fixed;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    filter: blur(120px);
    z-index: 0;
    pointer-events: none;
}
.stApp::before {
    background: radial-gradient(circle, rgba(240,147,251,0.25), transparent 70%);
    top: -100px;
    left: -100px;
    animation: orbFloat1 16s ease-in-out infinite;
}
.stApp::after {
    background: radial-gradient(circle, rgba(102,126,234,0.22), transparent 70%);
    bottom: -100px;
    right: -100px;
    animation: orbFloat2 20s ease-in-out infinite;
}
@keyframes orbFloat1 {
    0%, 100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(60px,40px) scale(1.15); }
}
@keyframes orbFloat2 {
    0%, 100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(-70px,-30px) scale(0.9); }
}

.block-container { padding-top: 2rem; padding-bottom: 4rem; position: relative; z-index: 1; }

/* ===== Animated hero ===== */
.hero {
    text-align: center;
    padding: 20px 0 10px;
    position: relative;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.18);
    color: #c4b5fd;
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
    animation: fadeDown 0.8s ease-out;
    backdrop-filter: blur(6px);
}
.hero-title {
    font-family: 'Sora', sans-serif;
    font-size: clamp(2.2rem, 6vw, 4rem);
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #f6d365, #fda085, #f093fb, #4facfe, #f6d365);
    background-size: 400% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 6s linear infinite, fadeUp 0.8s ease-out;
    margin: 0;
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    100% { background-position: 400% 50%; }
}
.hero-sub {
    color: #cbd5e1;
    font-size: 1.1rem;
    font-weight: 300;
    max-width: 600px;
    margin: 12px auto 0;
    animation: fadeUp 1s ease-out;
    opacity: 0.9;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== Feature chips ===== */
.feature-row {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin: 18px 0 6px;
}
.feature-chip {
    background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(240,147,251,0.2));
    border: 1px solid rgba(255,255,255,0.15);
    color: #e2e8f0;
    border-radius: 100px;
    padding: 8px 16px;
    font-size: 0.85rem;
    backdrop-filter: blur(6px);
    animation: fadeUp 1s ease-out both;
    transition: all 0.3s;
    cursor: pointer;
}
.feature-chip:hover {
    transform: translateY(-3px) scale(1.05);
    border-color: #f093fb;
    box-shadow: 0 8px 24px rgba(240,147,251,0.3);
}
.feature-chip:nth-child(1) { animation-delay: 0.1s; }
.feature-chip:nth-child(2) { animation-delay: 0.2s; }
.feature-chip:nth-child(3) { animation-delay: 0.3s; }
.feature-chip:nth-child(4) { animation-delay: 0.4s; }

/* ===== Glass card ===== */
.glass {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    animation: floatIn 0.6s ease-out;
    margin-bottom: 12px;
}
@keyframes floatIn {
    from { opacity: 0; transform: translateY(24px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ===== Animated stat cards ===== */
.stat-grid {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin: 20px 0;
}
.stat-card {
    flex: 1 1 150px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 18px;
    padding: 22px 16px;
    color: white;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    transition: transform 0.3s, box-shadow 0.3s;
    animation: popIn 0.5s ease-out both;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 40%);
    animation: shimmer 4s ease-in-out infinite;
}
@keyframes shimmer {
    0%, 100% { transform: translateX(-20%) translateY(-10%); opacity: 0.4; }
    50% { transform: translateX(20%) translateY(10%); opacity: 0.8; }
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.7); }
    to { opacity: 1; transform: scale(1); }
}
.stat-card:nth-child(1) { animation-delay: 0.05s; background: linear-gradient(135deg,#667eea,#764ba2); }
.stat-card:nth-child(2) { animation-delay: 0.15s; background: linear-gradient(135deg,#f093fb,#f5576c); }
.stat-card:nth-child(3) { animation-delay: 0.25s; background: linear-gradient(135deg,#43e97b,#38f9d7); }
.stat-card:nth-child(4) { animation-delay: 0.35s; background: linear-gradient(135deg,#fa709a,#fee140); }
.stat-card:hover { transform: translateY(-6px) scale(1.04); box-shadow: 0 18px 40px rgba(240,147,251,0.4); }
.stat-icon { font-size: 1.6rem; }
.stat-num { font-size: 2.4rem; font-weight: 800; line-height: 1; }
.stat-label { font-size: 0.8rem; opacity: 0.92; margin-top: 4px; letter-spacing: 0.5px; }

/* ===== Lesson cards with hover slide ===== */
.lesson-card {
    background: linear-gradient(135deg, #ffffff, #f8fafc);
    color: #1e293b;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 10px 0;
    border-left: 5px solid #667eea;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}
.lesson-card:hover {
    border-left-color: #f093fb;
    transform: translateX(8px);
    box-shadow: 0 8px 24px rgba(102,126,234,0.35);
}
.lesson-num {
    display: inline-block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: 700;
    margin-right: 10px;
}

/* ===== Buttons ===== */
.stButton > button {
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.65rem 1.2rem;
    transition: all 0.3s;
    box-shadow: 0 6px 20px rgba(102,126,234,0.4);
    position: relative;
    overflow: hidden;
}
.stButton > button::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: left 0.5s;
}
.stButton > button:hover::after { left: 100%; }
.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(240,147,251,0.5);
}

/* ===== Tabs ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.05);
    padding: 6px;
    border-radius: 100px;
    border: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 100px;
    padding: 12px 22px;
    font-weight: 600;
    color: #cbd5e1;
    transition: all 0.3s;
    border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { color: white; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #f093fb, #f5576c) !important;
    color: white !important;
    box-shadow: 0 6px 20px rgba(240,147,251,0.5);
}

/* ===== Headings / text ===== */
h1, h2, h3 { color: white; }
p, li { color: #e2e8f0; }
.css-1n543e5, [data-testid="stMarkdownContainer"] p { color: #e2e8f0; }

/* ===== Sidebar ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(15,12,41,0.97), rgba(36,36,62,0.97)) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
}
[data-testid="stSidebar"] * { color: #e2e8f0; }
[data-testid="stSidebar"] h3 { color: #f093fb; }

/* ===== Chat bubbles ===== */
.chat-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 14px 18px;
    margin: 8px 0;
    max-width: 85%;
    margin-left: auto;
    animation: popIn 0.35s ease-out;
    box-shadow: 0 6px 18px rgba(102,126,234,0.4);
}
.chat-bot {
    background: rgba(255,255,255,0.1);
    color: #f1f5f9;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px;
    margin: 8px 0;
    max-width: 85%;
    border: 1px solid rgba(255,255,255,0.15);
    backdrop-filter: blur(8px);
    animation: popIn 0.35s ease-out;
}

/* ===== Flashcard ===== */
.flashcard {
    background: linear-gradient(135deg, #ffecd2, #fcb69f);
    color: #1e293b;
    border-radius: 22px;
    padding: 36px;
    font-size: 1.2rem;
    text-align: center;
    min-height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 14px 40px rgba(0,0,0,0.35);
    margin: 12px 0;
    animation: cardFlip 0.5s ease-out;
    position: relative;
}
@keyframes cardFlip {
    0% { transform: perspective(800px) rotateY(90deg); opacity: 0; }
    100% { transform: perspective(800px) rotateY(0); opacity: 1; }
}

/* ===== Progress bar ===== */
.stProgress > div > div {
    background: rgba(255,255,255,0.1);
    border-radius: 100px;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #f093fb, #f5576c, #f6d365);
    border-radius: 100px;
    transition: width 0.5s ease;
}

/* ===== Feedback ===== */
.feedback-correct { color: #86efac; font-weight: 600; animation: fadeUp 0.4s; }
.feedback-wrong { color: #fca5a5; font-weight: 600; animation: fadeUp 0.4s; }

/* ===== Download / info boxes ===== */
.stDownloadButton > button {
    background: linear-gradient(135deg, #43e97b, #38f9d7);
    color: #064e3b;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    box-shadow: 0 6px 20px rgba(56,249,215,0.4);
    transition: all 0.3s;
}
.stDownloadButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(56,249,215,0.6);
}
[data-testid="stAlert"] {
    border-radius: 12px;
    backdrop-filter: blur(8px);
}
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    overflow: hidden;
}
[data-testid="stExpander"] summary { color: white; }
</style>
"""


def init_state():
    defaults = {
        "course_result": None,
        "course_json": None,
        "chat_history": [],
        "flashcard_index": 0,
        "quiz_attempts": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    secret_key = ""
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass

    with st.sidebar:
        st.markdown(
            "<h3>\U00002699\ufe0f Configuration</h3>",
            unsafe_allow_html=True,
        )
        if secret_key:
            st.success("\U0001f512 API key loaded from deployment secrets.")
        api_key = st.text_input(
            "OpenAI API Key", type="password", placeholder="sk-...",
            value=secret_key if secret_key else "", help="Loaded from secrets if deployed.",
        )
        model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0)
        temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)
        st.divider()
        st.markdown("#### \U0001f4cc How it works")
        st.markdown(
            "1\ufe0f\u20e3  **Input** — topic or document\n\n"
            "2\ufe0f\u20e3  **Generate** — AI builds your course\n\n"
            "3\ufe0f\u20e3  **Explore** — lessons, quiz, flashcards\n\n"
            "4\ufe0f\u20e3  **Ask** — AI tutor answers accurately"
        )
        if not api_key:
            st.warning("Add your API key to activate generation.")
    return api_key, model, temperature


def extract_text(uploaded) -> str:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".pdf":
        import PyPDF2
        reader = PyPDF2.PdfReader(uploaded)
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    return uploaded.read().decode("utf-8")


def generate_course(content, api_key, model, temperature):
    llm = LLMService(api_key=api_key, model=model, temperature=temperature)
    raw = llm.generate_course(content)
    return raw, CourseOutput.from_dict(raw).to_dict()


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">AI-Powered Learning</div>
            <h1 class="hero-title">CourseForge AI</h1>
            <div class="hero-sub">Turn any knowledge into a stunning interactive course — lessons,
            quizzes, flashcards & an AI tutor.</div>
            <div class="feature-row">
                <span class="feature-chip">\u2728 AI Generation</span>
                <span class="feature-chip">\U0001f4d6 Interactive Lessons</span>
                <span class="feature-chip">\U00002753 Smart Quizzes</span>
                <span class="feature-chip">\U0001f4a1 Flashcards</span>
                <span class="feature-chip">\U0001f4ac AI Tutor</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_cards(course):
    st.markdown("<div class='stat-grid'>", unsafe_allow_html=True)
    items = [
        ("\U0001f3af", len(course["learningObjectives"]), "Objectives"),
        ("\U0001f4d6", len(course["lessonOutline"]), "Lessons"),
        ("\U00002753", len(course["quizQuestions"]), "Quiz Q's"),
        ("\U0001f4ac", len(course["lessonSummaries"]), "Summaries"),
    ]
    st.markdown("".join(
        f"<div class='stat-card'><div class='stat-icon'>{ic}</div>"
        f"<div class='stat-num'>{n}</div><div class='stat-label'>{lbl}</div></div>"
        for ic, n, lbl in items
    ), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_overview(course):
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U0001f3af Learning Objectives")
    for obj in course["learningObjectives"]:
        st.markdown(f"\U0001f7e2 {obj}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U0001f4cf Lesson Outline")
    for i, lesson in enumerate(course["lessonOutline"], 1):
        st.markdown(
            f"<div class='lesson-card'><span class='lesson-num'>{i}</span>{lesson}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_lessons(course):
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U0001f4d6 Lesson Summaries")
    for i, summary in enumerate(course["lessonSummaries"], 1):
        title = course["lessonOutline"][i - 1] if i <= len(course["lessonOutline"]) else f"Lesson {i}"
        with st.expander(f"\U0001f4c5 {i}. {title}", expanded=(i == 1)):
            st.markdown(summary)
    st.markdown("</div>", unsafe_allow_html=True)


def render_quiz(course):
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U00002753 Interactive Quiz")
    total = len(course["quizQuestions"])
    score = sum(
        1 for q in course["quizQuestions"]
        if st.session_state.quiz_attempts.get(f"q{q['question']}") == q["correctAnswerIndex"]
    )
    answered = sum(
        1 for q in course["quizQuestions"]
        if f"q{q['question']}" in st.session_state.quiz_attempts
    )

    st.markdown(
        f"<div style='color:#e2e8f0;margin-bottom:6px'>Score: "
        f"<b style='color:#86efac'>{score}/{answered}</b></div>",
        unsafe_allow_html=True,
    )
    st.progress(answered / total if total else 0)

    for i, q in enumerate(course["quizQuestions"], 1):
        st.markdown(f"<div class='lesson-card'><b>Q{i}:</b> {q['question']}</div>", unsafe_allow_html=True)
        key = f"q{q['question']}"
        selected = st.radio(
            "Choose:", range(4), index=None,
            format_func=lambda x, qq=q: f"{chr(65 + x)}) {qq['options'][x]}",
            key=f"radio_{key}", label_visibility="collapsed",
        )
        if st.button(f"Submit Q{i}", key=f"submit_{key}"):
            if selected is not None:
                st.session_state.quiz_attempts[key] = selected
                st.rerun()
            else:
                st.warning("Select an answer first.")

        if key in st.session_state.quiz_attempts:
            chosen = st.session_state.quiz_attempts[key]
            correct = q["correctAnswerIndex"]
            if chosen == correct:
                st.markdown("<div class='feedback-correct'>\u2714 Correct!</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='feedback-wrong'>\u2716 Incorrect. Correct: "
                    f"{chr(65 + correct)}) {q['options'][correct]}</div>", unsafe_allow_html=True,
                )
            if q.get("explanation"):
                st.info(q["explanation"])
        st.markdown("<br>", unsafe_allow_html=True)

    if answered == total and total:
        pct = score / total
        if pct == 1.0:
            st.balloons()
            st.success("Perfect! \U0001f389 Mastery achieved!")
        elif pct >= 0.7:
            st.success("Great job! Keep going.")
        else:
            st.info("Review the lessons and try again.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_flashcards(course):
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U0001f4a1 Flashcards")
    items = [("Lesson", t, s) for t, s in zip(course["lessonOutline"], course["lessonSummaries"])]
    items += [
        ("Question", q["question"], f"{chr(65 + q['correctAnswerIndex'])}) {q['options'][q['correctAnswerIndex']]}")
        for q in course["quizQuestions"]
    ]

    if not items:
        st.info("No flashcards.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    idx = st.session_state.flashcard_index % len(items)
    ftype, front, back = items[idx]
    st.markdown(
        f"<div class='flashcard'>{'<b>' + ftype + '</b><br><br>' if ftype else ''}{front}</div>",
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
    st.markdown("</div>", unsafe_allow_html=True)


def render_ask(course, api_key, model, temperature):
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("\U0001f4ac Ask Your AI Tutor")
    st.markdown(
        "<span style='color:#e2e8f0'>Ask anything — get an <b>accurate</b> answer grounded in the "
        "course material.</span>",
        unsafe_allow_html=True,
    )
    content_section = "\n\n".join(course["lessonSummaries"])
    question = st.chat_input(f"Ask about {course['courseTitle']}...")

    if question and api_key:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.spinner("Tutor is thinking..."):
            try:
                llm = LLMService(api_key=api_key, model=model, temperature=temperature)
                answer = llm.answer_question(course["courseTitle"], content_section, question)
                st.session_state.chat_history.append({"role": "bot", "content": answer})
            except Exception as e:
                st.session_state.chat_history.append({"role": "bot", "content": f"Error: {e}"})
        st.rerun()

    for msg in st.session_state.chat_history:
        cls = "chat-user" if msg["role"] == "user" else "chat-bot"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    init_state()
    api_key, model, temperature = render_sidebar()

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    render_hero()

    tab_gen, tab_course, tab_quiz, tab_flash, tab_ask = st.tabs(
        ["\u2728 Generate", "\U0001f4d6 Course", "\U00002753 Quiz", "\U0001f4a1 Flashcards", "\U0001f4ac AI Tutor"]
    )

    course_result = st.session_state.course_result

    with tab_gen:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("\U0001f4e4 Create a Course")
        mode = st.radio("Input type:", ["Text Prompt", "Upload Document"], horizontal=True)
        content = None
        if mode == "Text Prompt":
            content = st.text_area(
                "Enter topic or content:", height=160,
                placeholder="e.g., Introduction to Quantum Mechanics, Machine Learning basics...",
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

        do_gen = st.button(
            "\U0001f680 Generate Course", type="primary", use_container_width=True,
            disabled=not (content and api_key),
        )
        if do_gen and content and api_key:
            with st.spinner("Crafting your course... \u23f3"):
                try:
                    _, result = generate_course(content, api_key, model, temperature)
                    st.session_state.course_result = result
                    st.session_state.course_json = json.dumps(result, indent=2, ensure_ascii=False)
                    st.session_state.chat_history = []
                    st.session_state.quiz_attempts = {}
                    st.balloons()
                    st.success("Course generated! Explore the tabs. \U0001f389")
                except Exception as e:
                    st.error(f"Generation failed: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        if course_result:
            st.markdown("---")
            st.markdown(
                f"<h2 style='text-align:center;color:#f093fb;animation:fadeUp .5s'>{course_result['courseTitle']}</h2>",
                unsafe_allow_html=True,
            )
            stat_cards(course_result)
            st.download_button(
                "Download Course JSON", data=st.session_state.course_json,
                file_name="course_output.json", mime="application/json", use_container_width=True,
            )

    with tab_course:
        if course_result:
            render_overview(course_result)
            render_lessons(course_result)
        else:
            st.info("No course yet. Generate one in the \u2728 Generate tab.")

    with tab_quiz:
        if course_result:
            render_quiz(course_result)
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
