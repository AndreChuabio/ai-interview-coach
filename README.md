# AI Interview Coach

Practice interviews with a voice-based AI interviewer that analyzes your responses, tone, and facial expressions in real time, then delivers a comprehensive feedback report.

Built for the Fordham University AI Solutions Challenge (Spring 2026).

## Key Features

- **Voice-based AI interviewer**: Speak naturally with an AI that asks follow-up questions based on your responses
- **Facial expression tracking**: MediaPipe Face Mesh runs in-browser to detect eye contact, emotions, and fidgeting
- **Tone analysis**: librosa-powered audio analysis measures speaking pace, filler words, pitch, and energy
- **Comprehensive feedback report**: Post-interview report with content scoring, communication metrics, and body language analysis
- **Provider-agnostic**: Swap LLM, STT, and TTS providers by changing a single environment variable

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
                                           +----------------------+
```

## Provider Abstraction

Every external API sits behind an abstract interface. Swap providers via `.env`:

| Service | Free Option | Paid Options |
|---------|-------------|--------------|
| LLM     | Gemini 2.0 Flash (free tier) | OpenAI GPT-4o, Anthropic Claude, Ollama (local) |
| STT     | Local Whisper (offline)       | OpenAI Whisper API, Deepgram, Google Cloud STT |
| TTS     | edge-tts (free)              | OpenAI TTS, ElevenLabs, Google Cloud TTS |

Zero-cost development stack: Gemini free tier + local Whisper + edge-tts = $0.

## Project Structure

```
ai-interview-coach/
├── frontend/                    # Next.js + Tailwind CSS + shadcn/ui
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
│   │   ├── interview_agent.py   # LLM conversation engine
│   │   ├── tone_analyzer.py     # librosa audio analysis
│   │   ├── face_aggregator.py   # Facial expression aggregation
│   │   └── feedback_engine.py   # Report generation
│   ├── providers/               # Swappable API provider layer
│   │   ├── base.py              # ABC interfaces
│   │   ├── factory.py           # Provider factory
│   │   ├── llm/                 # Gemini, OpenAI, Anthropic, Ollama
│   │   ├── stt/                 # Whisper (local/API), Deepgram, Google
│   │   └── tts/                 # edge-tts, OpenAI, ElevenLabs, Google
│   └── prompts/                 # Interview prompts (behavioral, technical, case)
├── requirements.txt
└── .env.example
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Google API key (for Gemini free tier) OR any supported LLM provider key

### Backend Setup

```bash
cd ai-interview-coach

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure providers
cp .env.example .env
# Edit .env with your API key(s)

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd ai-interview-coach/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open http://localhost:3000 to start practicing.

## Interview Types

- **Behavioral**: STAR method evaluation, leadership, teamwork, conflict resolution
- **Technical**: Data science, coding, SQL, system design
- **Case Study**: Market sizing, profitability, strategy frameworks

## Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS, Recharts, MediaPipe Face Mesh
- **Backend**: FastAPI, Pydantic, librosa, NumPy
- **LLM**: Google Gemini / OpenAI / Anthropic / Ollama (configurable)
- **STT**: Local Whisper / OpenAI Whisper API / Deepgram (configurable)
- **TTS**: edge-tts / OpenAI TTS / ElevenLabs (configurable)

## Current Status

Phase 1-2 complete:
- Voice conversation pipeline (STT -> LLM -> TTS) working end-to-end
- Provider abstraction layer with free-tier defaults
- MediaPipe face tracking with real-time expression indicators
- librosa tone analysis (pace, fillers, pitch, energy)
- Interview setup UI with type/role/company/difficulty selection
- Real-time transcript with per-turn tone metrics
- Face tracker sidebar with eye contact and emotion detection

Phase 3-4 pending:
- Comprehensive feedback report generation
- Paid provider implementations (OpenAI, Deepgram, ElevenLabs)
- Deployment to Vercel + Railway
- UI polish and demo preparation

## Author

Andre Chuabio
Email: andre102599@gmail.com
GitHub: https://github.com/AndreChuabio

## License

MIT
