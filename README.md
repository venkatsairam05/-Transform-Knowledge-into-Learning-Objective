# Knowledge to Course Generator

An AI-powered application that transforms knowledge from documents or text prompts into structured learning courses using OpenAI's GPT models.

## Features

- **Multiple Input Sources**: Accept PDF files, plain text files (.txt, .md), or direct text prompts
- **Structured Output**: Generates a complete course with title, learning objectives, lesson outline, quiz questions, and lesson summaries — all in valid JSON
- **Robust Error Handling**: Retries on API failures, validates input and output, handles malformed responses
- **Configurable**: Choose model, temperature, and output path via CLI arguments
- **Two Entry Points**: CLI module (`python -m src`) or standalone script (`python run.py`)

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| LLM Provider | OpenAI (GPT-4o) |
| PDF Processing | PyPDF2 |
| Configuration | python-dotenv |

## Prerequisites

- Python 3.10 or higher
- An OpenAI API key with access to GPT-4o (or GPT-4o-mini)
- pip (Python package manager)

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/knowledge-to-course.git
cd knowledge-to-course
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Never commit your `.env` file or API keys to version control.**

## How to Run

### Option A: Using the CLI Module

```bash
# From a text prompt
python -m src --prompt "Introduction to Python programming"

# From a PDF file
python -m src --file input/sample.pdf

# From a text file
python -m src --file input/quantum_mechanics.txt

# With custom model and output path
python -m src --prompt "Machine Learning basics" --model gpt-4o-mini --output output/ml_course.json
```

### Option B: Using the Standalone Script

```bash
# From a text prompt
python run.py --prompt "Introduction to Quantum Mechanics"

# From a file
python run.py --file input/quantum_mechanics.txt

# Custom model and temperature
python run.py --prompt "Data Structures and Algorithms" --model gpt-4o-mini --temperature 0.5
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--prompt`, `-p` | Text prompt describing the topic | (mutually exclusive with `--file`) |
| `--file`, `-f` | Path to input file (.pdf, .txt, .md) | (mutually exclusive with `--prompt`) |
| `--output`, `-o` | Output JSON file path | `output/course_<timestamp>.json` |
| `--model`, `-m` | OpenAI model identifier | `gpt-4o` |
| `--temperature`, `-t` | Generation temperature | `0.7` |

## How the API Integration Works

### 1. Prompt Construction (`src/prompt_engineer.py`)

A system prompt establishes the LLM's role as an instructional designer and specifies the exact JSON schema expected. The user prompt wraps the input content and instructs the LLM to respond with only the JSON object.

### 2. LLM API Call (`src/llm_service.py`)

The application uses the OpenAI Chat Completions API with `response_format={"type": "json_object"}` to enforce JSON output. It passes the constructed messages and requests up to 4096 tokens.

### 3. Response Parsing and Validation

The raw LLM response is parsed by extracting the JSON object (handling markdown code fences if present). The parsed dictionary is validated against the required schema:
- All required fields are present
- Exactly 5 quiz questions exist
- Each question has exactly 4 options
- `correctAnswerIndex` is 0-3

### 4. Error Handling and Retries

- **Rate limit / connection errors**: Exponential backoff with up to 3 retries
- **Server errors (5xx)**: Retried with backoff
- **Client errors (4xx)**: Failed immediately with descriptive error
- **Malformed JSON**: Retried (the LLM is re-prompted)
- **Schema validation failure**: Retried

### 5. Structured Output Extraction

The validated dictionary is converted into a `CourseOutput` dataclass for type safety, then serialized to JSON with `json.dump()` for the final output file.

## Example Input

**Text prompt:** "Introduction to Quantum Mechanics"

**Or file content** (`input/quantum_mechanics.txt`):
```
Quantum mechanics is a fundamental theory in physics that provides a description
of the physical properties of nature at the scale of atoms and subatomic particles...
[content about wave-particle duality, uncertainty principle, Schrödinger equation, etc.]
```

## Example Output

The generated `course_output.json`:

```json
{
  "courseTitle": "Introduction to Quantum Mechanics",
  "learningObjectives": [
    "Understand the fundamental principles of quantum mechanics",
    "Explain the concept of quantization and its historical significance",
    "Analyze the Schrödinger equation and its role in quantum systems",
    "Describe quantum phenomena such as superposition and entanglement",
    "Identify real-world applications of quantum mechanics"
  ],
  "lessonOutline": [
    "1. Foundations of Quantum Theory",
    "2. Wave-Particle Duality and the Uncertainty Principle",
    "3. Quantization and Energy Levels",
    "4. The Schrödinger Equation and Wave Functions",
    "5. Superposition, Entanglement, and Applications"
  ],
  "quizQuestions": [
    {
      "question": "What does the principle of wave-particle duality state?",
      "options": [
        "All quantum entities exhibit both wave-like and particle-like properties",
        "Particles can only behave as particles, never as waves",
        "Waves and particles are fundamentally different phenomena",
        "Quantum objects behave as waves during measurement only"
      ],
      "correctAnswerIndex": 0,
      "explanation": "Wave-particle duality states that all quantum entities display both wave-like and particle-like characteristics."
    }
  ],
  "lessonSummaries": [
    "This lesson introduces the origins of quantum mechanics and why classical physics was insufficient...",
    "This lesson covers wave-particle duality and the Heisenberg uncertainty principle...",
    "This lesson explains quantization — that energy comes in discrete units called quanta...",
    "This lesson dives into the Schrödinger equation, the central equation of quantum mechanics...",
    "This lesson explores superposition and entanglement, plus practical applications..."
  ]
}
```

A complete sample is included in `course_output.json`.

## Design Decisions and Architectural Approach

### Architecture

The application follows a **modular pipeline architecture** with clear separation of concerns:

```
Input (text/file) → DocumentProcessor → PromptEngineer → LLMService → Validation → CourseOutput
```

| Module | Responsibility |
|--------|---------------|
| `src/models.py` | Data models (`CourseOutput`, `QuizQuestion`) with serialization |
| `src/document_processor.py` | Input handling — PDF extraction, text reading, truncation |
| `src/prompt_engineer.py` | Prompt construction and raw response parsing |
| `src/llm_service.py` | OpenAI API integration with retry logic and schema validation |
| `src/course_generator.py` | Orchestration — ties all components together |
| `src/main.py` | CLI interface with argparse |

### Key Design Choices

1. **OpenAI API**: Chosen for its reliability, wide availability, native JSON mode support (`response_format`), and strong structured output capabilities.

2. **Structured JSON mode**: Using `response_format={"type": "json_object"}` ensures the LLM returns parseable JSON, reducing the likelihood of malformed responses.

3. **Retry with exponential backoff**: Handles transient failures (rate limits, network issues, server errors) gracefully without immediate failure.

4. **Dual validation**: The LLM is given a strict schema in the prompt, and the response is programmatically validated. This two-layer approach significantly improves reliability.

5. **Dataclass models**: Provides type safety and clean serialization/deserialization, making the output contract explicit and enforceable.

## External Libraries and Dependencies

| Library | Purpose |
|---------|---------|
| `openai` (v1.0+) | Official OpenAI Python SDK for API communication |
| `PyPDF2` (v3.0+) | PDF text extraction |
| `python-dotenv` (v1.0+) | Loading environment variables from `.env` files |

## Assumptions, Limitations, and Future Improvements

### Assumptions
- The OpenAI API is available and the user has valid API credits
- Input documents contain meaningful text content (not image-only PDFs)
- English is the primary language for both input and output

### Limitations
- PDF extraction cannot handle scanned documents (would need OCR)
- The quality of generated courses depends on the input content quality
- Long documents are truncated to 50,000 characters
- Only supports one input source per run (no multi-file consolidation)

### Future Improvements
- Support for additional LLM providers (Anthropic Claude, Google Gemini)
- Multi-file input consolidation
- OCR support for scanned PDFs
- Web-based UI with Streamlit or FastAPI
- Support for more quiz question types (true/false, fill-in-the-blank)
- Course progress tracking and adaptive content generation
- Streaming response for real-time output display
- Support for additional output formats (Markdown, HTML)
