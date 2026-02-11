# AI Interview Coach

Practice interviews with a voice-based AI interviewer that analyzes your responses, tone, and facial expressions in real time, then delivers a comprehensive feedback report.

Built for the Fordham University AI Solutions Challenge (Spring 2026).

## Key Features

- **Voice-based AI interviewer** -- speak naturally; the AI asks follow-up questions based on your answers
- **Facial expression tracking** -- MediaPipe Face Mesh runs in-browser to detect eye contact, emotions, and head pose
- **Tone analysis** -- librosa-powered audio analysis measures speaking pace, filler words, pitch, energy, and silence
- **Comprehensive feedback report** -- post-interview report with content scoring, communication metrics, body language analysis, and radar chart
- **Provider-agnostic** -- swap LLM, STT, and TTS providers by changing a single environment variable (zero-cost defaults included)

## Architecture

```
Browser (Next.js)                          Backend (FastAPI)
+--------------------+                     +----------------------+
| Interview UI       | -- audio blob -->   | STT Provider (ABC)   |
| Webcam + MediaPipe | -- face data -->    | Interview Agent      |
| Audio Recorder     | <-- TTS audio ---   | TTS Provider (ABC)   |
+--------------------+                     | LLM Provider (ABC)   |
                                           | Tone Analyzer        |
                                           | Feedback Engine      |
                                           +---+------------------+
                                               |
                               +---------------+----------------+
                               |               |                |
                         +-----v----+   +------v------+  +------v------+
                         | Neo4j    |   | SQLite/     |  | Embedder    |
                         | AuraDB   |   | PostgreSQL  |  | MiniLM-L6   |
                         | (Graph + |   | (Sessions,  |  | (sentence-  |
                         | Vectors) |   |  Reports)   |  | transformers|
                         +----------+   +-------------+  +-------------+
```

## Provider Abstraction

Every external AI service sits behind an abstract base class. Swap providers via `.env` -- no code changes needed:

| Service | Free Option (default) | Paid Options |
|---------|----------------------|--------------|
| LLM     | Gemini 2.5 Flash (free tier) | OpenAI GPT-4o, Anthropic Claude, Ollama (local) |
| STT     | Local Whisper (offline) | OpenAI Whisper API, Deepgram, Google Cloud STT |
| TTS     | edge-tts (free) | OpenAI TTS, ElevenLabs, Google Cloud TTS |

Zero-cost development stack: Gemini free tier + local Whisper + edge-tts = $0.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- ffmpeg (required by Whisper for audio processing)
- A free Google API key from [Google AI Studio](https://aistudio.google.com/apikey)

Install ffmpeg if you don't have it:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

### 1. Clone and configure

```bash
git clone https://github.com/AndreChuabio/ai-interview-coach.git
cd ai-interview-coach

# Set up environment variables
cp .env.example .env
```

Open `.env` and paste your Google API key:

```
GOOGLE_API_KEY=your_key_here
```

That is the only required configuration. Everything else has working defaults.

### 2. Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn backend.main:app --reload --port 8000
```

The first run downloads the Whisper `base` model (~140 MB). Subsequent starts are instant.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Use it

Open **http://localhost:3000** in your browser. Select an interview type, role, and company, then click Start Interview. Allow microphone and camera access when prompted.

## Project Structure

```
ai-interview-coach/
├── frontend/                    # Next.js + Tailwind CSS
│   ├── src/app/                 # App router pages
│   ├── src/components/          # React components
│   │   ├── InterviewSetup.tsx   # Role/company/type selector
│   │   ├── InterviewSession.tsx # Voice interview with real-time indicators
│   │   ├── FaceTracker.tsx      # MediaPipe webcam + expression tracking
│   │   └── FeedbackReport.tsx   # Post-interview report with charts
│   └── src/lib/                 # API client, audio helpers, MediaPipe
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Provider selection via .env
│   ├── routers/                 # API endpoints (interview, feedback)
│   ├── services/                # Business logic
│   │   ├── interview_agent.py   # LLM conversation + RAG integration
│   │   ├── tone_analyzer.py     # librosa audio analysis
│   │   ├── face_aggregator.py   # Facial expression aggregation
│   │   └── feedback_engine.py   # Report generation + RAG benchmarking
│   ├── providers/               # Swappable AI provider layer
│   │   ├── base.py              # Abstract base classes (LLM, STT, TTS)
│   │   ├── factory.py           # Provider factory (reads .env)
│   │   ├── llm/                 # Gemini, OpenAI, Anthropic, Ollama
│   │   ├── stt/                 # Whisper local, Whisper API, Deepgram
│   │   └── tts/                 # edge-tts, OpenAI TTS, ElevenLabs
│   ├── db/                      # Persistence layer
│   │   ├── engine.py            # SQLAlchemy async engine (SQLite/PostgreSQL)
│   │   ├── models.py            # ORM models (sessions, reports)
│   │   └── session_store.py     # Dual-write store (cache + DB)
│   ├── knowledge/               # Knowledge graph + RAG
│   │   ├── graph.py             # Neo4j connection manager + queries
│   │   ├── embedder.py          # sentence-transformers embeddings
│   │   ├── retriever.py         # Hybrid retriever (graph + vector)
│   │   ├── seeder.py            # Neo4j seed script
│   │   └── seed_data.py         # Curated questions, answers, companies
│   ├── prompts/                 # System prompts per interview type
│   └── data/                    # Question bank (JSON)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Interview Types

- **Behavioral** -- STAR method evaluation, leadership, teamwork, conflict resolution
- **Technical** -- data science, coding, SQL, system design
- **Case Study** -- market sizing, profitability, strategy frameworks

## Switching Providers

Edit `.env` to swap any provider. Example -- switch from Gemini to OpenAI:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

Or use a fully local stack with Ollama:

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_URL=http://localhost:11434
```

No code changes required. Restart the backend after editing `.env`.

## Knowledge Graph (RAG)

When Neo4j is configured, the interview agent and feedback engine are enriched with:
- **Company-specific context** -- questions actually asked at target companies
- **Role-targeted questions** -- matched via graph relationships (Question -> Role, Question -> Company)
- **Semantic search** -- vector similarity on question/answer embeddings (all-MiniLM-L6-v2, 384-dim)
- **Example answer benchmarking** -- feedback engine compares candidate responses against curated strong answers

The RAG layer is optional. Without Neo4j credentials, the app falls back to the static question bank.

To seed the knowledge graph:

```bash
python -m backend.knowledge.seeder
```

## Session Persistence

Sessions and feedback reports are persisted to a SQL database via SQLAlchemy:
- **Local dev**: SQLite (zero setup, default)
- **Production**: Swap to PostgreSQL by changing one line in `.env`

```bash
# .env for production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/interview_coach
```

## Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS, Recharts, MediaPipe Face Mesh
- **Backend**: FastAPI, Pydantic, SQLAlchemy, librosa, NumPy
- **Knowledge Graph**: Neo4j AuraDB (graph traversal + vector index)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **LLM**: Google Gemini / OpenAI / Anthropic / Ollama (configurable)
- **STT**: Local Whisper / OpenAI Whisper API / Deepgram (configurable)
- **TTS**: edge-tts / OpenAI TTS / ElevenLabs (configurable)

## Current Status

Phase 1-2 complete (voice pipeline + real-time analysis):
- Voice conversation pipeline (STT -> LLM -> TTS) working end-to-end
- Provider abstraction layer with free-tier defaults and retry logic
- MediaPipe face tracking with real-time expression indicators
- librosa tone analysis (pace, fillers, pitch, energy, silence ratio)
- Interview setup UI with type/role/company/difficulty selection
- Live transcript with per-turn tone metrics
- Face tracker sidebar with eye contact and emotion detection
- Feedback report page with radar chart and per-category scoring

Phase 3 complete (knowledge graph + persistence):
- Neo4j AuraDB knowledge graph with 15 companies, 12 roles, 16 topics, 14 questions, example answers
- Hybrid RAG retriever (graph traversal + cosine vector search on 384-dim embeddings)
- Interview agent enriched with company-specific and role-targeted context from Neo4j
- Feedback engine benchmarks candidate answers against curated example responses
- Session and report persistence via SQLAlchemy (SQLite dev / PostgreSQL prod)
- Seeder script for populating the knowledge graph with embeddings

Phase 4 planned:
- Deployment to Vercel (frontend) + Railway (backend)
- UI polish and demo video

## Author

Andre Chuabio -- [GitHub](https://github.com/AndreChuabio) -- andre102599@gmail.com

## License

MIT
