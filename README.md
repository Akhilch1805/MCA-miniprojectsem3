# ⚡ PathForge AI — Personalized Learning Path Generator

> **AI-powered career acceleration.** Four specialized AI agents analyze your skills, build a personalized learning roadmap, curate the best resources, and adapt as you grow.

---

## 🚀 Quick Start

### 1. Clone & enter the repo

```bash
git clone <your-repo-url>
cd MCA-miniprojectsem3
```

### 2. Set up Python environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your Groq API key (free at https://console.groq.com/)
```

### 4. Start the server

```bash
python api.py
# or: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open the app

| URL | Description |
|-----|-------------|
| **http://localhost:8000/** | 🌐 PathForge AI — Landing Page |
| **http://localhost:8000/static/pages/app.html** | 🎯 App — Generate Learning Path |
| **http://localhost:8000/docs** | 📖 FastAPI Swagger UI |
| **http://localhost:8000/health** | ✅ Health Check |

Or open the HTML directly (no server needed for the UI):
```bash
open frontend/index.html
```
> ⚠️ When opening directly, the API calls still need the FastAPI server running at `localhost:8000`.

---

## 🤖 AI Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **Profiler & Diagnostic Specialist** | Analyzes your skills, identifies critical gaps, ranks them by priority |
| 2 | **Curriculum Architect** | Designs a sequenced 4–8 module roadmap with milestones & capstone project |
| 3 | **Resource Curation Specialist** | Attaches vetted free/paid resources, exercises & official docs per module |
| 4 | **Assessment & Adaptive Learning Specialist** | Generates 7-question quizzes and adapts upcoming modules to your performance |

---

## 🗂️ Project Structure

```
MCA-miniprojectsem3/
├── api.py              # FastAPI backend (serves frontend + REST API)
├── agents.py           # 4 CrewAI agent definitions
├── tasks.py            # 4 CrewAI task definitions
├── crew.py             # Pipeline assembly & execution
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
│
└── frontend/           # Production HTML/CSS/JS frontend
    ├── index.html      # Landing page (PathForge AI)
    ├── pages/
    │   └── app.html    # Main app (profile → generate → results → quiz)
    └── assets/
        ├── style.css   # Global design system (dark glassmorphism)
        ├── landing.js  # Landing page animations & particle system
        └── app.js      # App logic + FastAPI integration
```

---

## 🔌 API Reference

### `POST /generate`
Run the full 4-agent pipeline.

**Body:**
```json
{
  "name": "Akhil",
  "current_skills": ["Python", "SQL", "HTML/CSS"],
  "experience_years": 1,
  "target_role": "Machine Learning Engineer",
  "weekly_hours": 15,
  "generate_quiz_for_module": 1
}
```

**Response:** `gap_report`, `roadmap`, `enriched_roadmap`, `assessment` (all in Markdown)

---

### `POST /assess`
Submit quiz answers and receive an adaptation report.

**Body:**
```json
{
  "module_number": 1,
  "enriched_roadmap": "<roadmap text from /generate>",
  "answers": { "q1": "B", "q2": "Gradient descent..." }
}
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ (or OpenAI) | Your Groq API key (recommended — free tier) |
| `GROQ_MODEL` | Optional | Groq model name (default: `qwen/qwen3.8-27b`) |
| `OPENAI_API_KEY` | Alternative | OpenAI API key (fallback if no Groq key) |
| `OPENAI_MODEL` | Optional | OpenAI model (default: `gpt-4o`) |
| `CREWAI_DISABLE_TELEMETRY` | Optional | Set `true` to disable anonymous usage stats |

---

## 🏗️ Tech Stack

- **Backend:** Python, FastAPI, CrewAI ≥1.15, Groq/OpenAI via LiteLLM
- **Frontend:** Vanilla HTML5, CSS3 (glassmorphism design system), JavaScript (ES2022)
- **Markdown rendering:** marked.js (CDN)
- **Deployment:** Single `uvicorn` process serves both the API and frontend

---

## 📄 License

MIT — free for personal and commercial use.