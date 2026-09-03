/* CourseForge AI frontend logic */

let course = null;
let flashIndex = 0;
let flashFlipped = false;
let quizAnswers = {};
let selectedProvider = 'openai';

const $ = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', init);

function init() {
  // Mode toggle
  $('modeText').addEventListener('click', () => setMode('text'));
  $('modeFile').addEventListener('click', () => setMode('file'));
  $('generateBtn').addEventListener('click', handleGenerate);
  $('fileInput').addEventListener('change', handleFileUpload);

  // Provider toggle
  $('providerOpenAI').addEventListener('click', () => setProvider('openai'));
  $('providerGemini').addEventListener('click', () => setProvider('gemini'));

  // Tab bar
  document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));
}

function setProvider(name) {
  selectedProvider = name;
  document.querySelectorAll('.provider-btn').forEach(b => b.classList.toggle('active', b.dataset.provider === name));
}

function setMode(mode) {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  $('contentInput').style.display = (mode === 'text') ? '' : 'none';
  $('fileRow').style.display = (mode === 'file') ? '' : 'none';
}

function showError(msg) {
  const box = $('errorBox');
  box.textContent = msg;
  box.style.display = 'block';
}

function clearError() { $('errorBox').style.display = 'none'; }

function getApiKey() { return $('apiKeyInput').value.trim(); }

function showLoading(on) {
  const btn = $('generateBtn');
  btn.disabled = on;
  if (on) { btn.innerHTML = '<span class="spinner"></span> Generating...'; btn.classList.add('loading'); }
  else { btn.innerHTML = '🚀 Generate Course'; btn.classList.remove('loading'); }
}

async function handleGenerate() {
  clearError();
  let content = $('contentInput').value.trim();
  if (!content) { showError('Please enter some content or select a file first.'); return; }
  showLoading(true);
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, apiKey: getApiKey(), provider: selectedProvider })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Generation failed.');
    course = data.course;
    course.provider = selectedProvider;
    renderCourse();
  } catch (e) {
    showError(e.message);
  } finally { showLoading(false); }
}

async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed.');
    $('contentInput').value = data.content;
    $('contentInput').style.display = '';
    setMode('text');
    document.querySelector('[data-mode="text"]').classList.add('active');
    document.querySelector('[data-mode="file"]').classList.remove('active');
    $('fileRow').style.display = 'none';
  } catch (e) { showError(e.message); }
}

function renderCourse() {
  $('resultSection').style.display = '';
  $('courseTitle').textContent = course.courseTitle;
  renderStats();
  renderLessons();
  renderQuiz();
  renderFlashcards();
  renderAsk();
  switchTab('lessons');
  window.scrollTo({ top: $('resultSection').offsetTop - 20, behavior: 'smooth' });
}

function renderStats() {
  const items = [
    ['🎯', course.learningObjectives.length, 'Objectives'],
    ['📖', course.lessonOutline.length, 'Lessons'],
    ['❓', course.quizQuestions.length, 'Quiz Q\'s'],
    ['💬', course.lessonSummaries.length, 'Summaries'],
  ];
  $('statsRow').innerHTML = items.map(([ic, n, l]) =>
    `<div class="stat-card"><div class="stat-icon">${ic}</div><div class="stat-num">${n}</div><div class="stat-label">${l}</div></div>`
  ).join('');
}

function renderLessons() {
  $('objectivesBox').innerHTML =
    '<div class="subheading">🎯 Learning Objectives</div>' +
    course.learningObjectives.map(o => `<div class="obj-item">🟢 ${o}</div>`).join('');

  $('outlineBox').innerHTML =
    '<div class="subheading">📌 Lesson Outline</div>' +
    course.lessonOutline.map((l, i) => `<div class="lesson-card"><span class="lesson-num">${i + 1}</span>${l}</div>`).join('');

  $('summariesBox').innerHTML =
    '<div class="subheading">📖 Lesson Summaries</div>' +
    course.lessonSummaries.map((s, i) => {
      const title = course.lessonOutline[i] || `Lesson ${i + 1}`;
      return `<div class="summary-item"><h4>📅 ${i + 1}. ${title.replace(/^\d+\.\s*/, '')}</h4>${s}</div>`;
    }).join('');
}

function renderQuiz() {
  quizAnswers = {};
  let html = '<div class="subheading">❓ Take the Quiz</div><div class="quiz-score" id="quizScore">Score: 0 / 0</div>';
  html += course.quizQuestions.map((q, i) => {
    const letters = ['A', 'B', 'C', 'D'];
    return `
      <div class="quiz-q">
        <div class="qtext">Q${i + 1}: ${q.question}</div>
        ${q.options.map((opt, j) =>
          `<button class="opt" id="q${i}_${j}" onclick="selectAnswer(${i},${j})">${letters[j]}) ${opt}</button>`
        ).join('')}
        <div class="expl" id="expl${i}" style="display:none;"></div>
      </div>`;
  }).join('');
  html += '<div class="win" id="winBox"></div>';
  $('quizBox').innerHTML = html;
}

function selectAnswer(qi, optIdx) {
  const q = course.quizQuestions[qi];
  quizAnswers[qi] = optIdx;

  // reset styling
  for (let j = 0; j < q.options.length; j++) {
    const el = $('q' + qi + '_' + j);
    el.className = 'opt';
  }
  $('q' + qi + '_' + optIdx).className = 'opt selected';
  const elem = $('q' + qi + '_' + optIdx);
  elem.className = (optIdx === q.correctAnswerIndex) ? 'opt correct' : 'opt wrong';
  const correctEl = $('q' + qi + '_' + q.correctAnswerIndex);
  if (optIdx !== q.correctAnswerIndex) correctEl.className = 'opt correct';

  const expl = $('expl' + qi);
  expl.style.display = '';
  if (optIdx === q.correctAnswerIndex) {
    expl.innerHTML = `<b style="color:#16a34a">✅ Correct!</b> ${q.explanation || ''}`;
  } else {
    expl.innerHTML = `<b style="color:#dc2626">❌ Incorrect.</b> Correct: ${String.fromCharCode(65 + q.correctAnswerIndex)}) ${q.options[q.correctAnswerIndex]}. ${q.explanation || ''}`;
  }
  updateScore();
}

function updateScore() {
  const answered = Object.keys(quizAnswers).length;
  const correct = course.quizQuestions.filter((q, i) => quizAnswers[i] === q.correctAnswerIndex).length;
  $('quizScore').textContent = `Score: ${correct} / ${answered}`;

  if (answered === course.quizQuestions.length) {
    const win = $('winBox');
    if (correct === course.quizQuestions.length) {
      win.innerHTML = `<div class="success">🎉 Perfect score! Mastery achieved!</div>`;
    } else if (correct / course.quizQuestions.length >= 0.7) {
      win.innerHTML = `<div class="success">👍 Great job! Keep going.</div>`;
    } else {
      win.innerHTML = `<div class="error">📚 Review the lessons and try again.</div>`;
    }
  }
}

function renderFlashcards() {
  const items = [];
  course.lessonOutline.forEach((t, i) => {
    if (course.lessonSummaries[i]) items.push({ type: 'Lesson', front: t, back: course.lessonSummaries[i] });
  });
  course.quizQuestions.forEach(q => {
    items.push({ type: 'Question', front: q.question, back: `${String.fromCharCode(65 + q.correctAnswerIndex)}) ${q.options[q.correctAnswerIndex]}` });
  });
  course.flashItems = items;
  flashIndex = 0; flashFlipped = false;
  $('flashBox').innerHTML =
    '<div class="subheading">💡 Review with Flashcards</div>' +
    '<div class="flash-container">' +
      `<div class="flashcard" onclick="flipFlash()"><span class="ftype" id="flashType"></span><span id="flashFront"></span></div>` +
      '<div class="flash-controls">' +
        '<button onclick="flashMove(-1)">⬅ Prev</button>' +
        '<button onclick="flipFlash()">👁 Reveal</button>' +
        '<button onclick="flashMove(1)">Next ➡</button>' +
      '</div>' +
      '<div class="flash-count" id="flashCount"></div>' +
    '</div>';
  renderFlash();
}

function flipFlash() { flashFlipped = !flashFlipped; renderFlash(); }
function flashMove(dir) {
  const n = course.flashItems.length;
  flashIndex = (flashIndex + dir + n) % n;
  flashFlipped = false;
  renderFlash();
}
function renderFlash() {
  const item = course.flashItems[flashIndex];
  $('flashType').textContent = item.type;
  $('flashFront').textContent = flashFlipped ? item.back : item.front;
  $('flashCount').textContent = `Card ${flashIndex + 1} of ${course.flashItems.length}`;
}

function renderAsk() {
  let html =
    '<div class="subheading">💬 Ask Your AI Tutor</div>' +
    '<div style="color:#e2e8f0;margin-bottom:12px;">Ask anything — get an accurate answer grounded in the course material.</div>' +
    '<div class="chat-box" id="chatBox"></div>' +
    '<div class="chat-input-row">' +
      '<input type="text" id="chatInput" placeholder="Ask a question...">' +
      '<button onclick="askQuestion()">Send</button>' +
    '</div>';
  $('askBox').innerHTML = html;
  document.getElementById('chatInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') askQuestion(); });
}

async function askQuestion() {
  const input = document.getElementById('chatInput');
  const q = input.value.trim();
  if (!q) return;
  addMsg('user', q);
  input.value = '';
  const typing = addMsg('bot', '<span class="spinner"></span> Thinking...');
  try {
    const res = await fetch('/api/ask', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, course, apiKey: getApiKey(), provider: (course && course.provider) || selectedProvider })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed.');
    document.getElementById('chatBox').removeChild(typing);
    addMsg('bot', data.answer);
  } catch (e) {
    document.getElementById('chatBox').removeChild(typing);
    addMsg('bot', 'Error: ' + e.message);
  }
}

function addMsg(role, content) {
  const box = document.getElementById('chatBox');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  ['lessons', 'quiz', 'flash', 'ask'].forEach(t => {
    $('tab-' + t).style.display = (t === tab) ? '' : 'none';
  });
}
