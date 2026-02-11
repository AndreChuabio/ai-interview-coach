"""
Application configuration loaded from environment variables.
Swap providers by changing values in .env -- zero code changes needed.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for the AI Interview Coach backend."""

    # -- LLM Provider --
    llm_provider: str = Field(default="gemini", description="LLM provider: gemini, openai, anthropic, ollama")
    llm_model: str = Field(default="gemini-2.0-flash", description="Model name within the chosen provider")

    # -- STT Provider --
    stt_provider: str = Field(default="local_whisper", description="STT provider: local_whisper, whisper_api, deepgram, google_stt")
    stt_model: str = Field(default="base", description="Whisper model size for local: tiny, base, small, medium, large")

    # -- TTS Provider --
    tts_provider: str = Field(default="edge_tts", description="TTS provider: edge_tts, openai_tts, elevenlabs, google_tts")
    tts_voice: str = Field(default="en-US-GuyNeural", description="Default voice identifier for TTS")

    # -- API Keys (only needed for the providers you select) --
    google_api_key: str = Field(default="", description="Google Gemini API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    deepgram_api_key: str = Field(default="", description="Deepgram API key")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key")

    # -- Ollama (local LLM) --
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama server URL")

    # -- Neo4j (Knowledge Graph / RAG) --
    neo4j_uri: str = Field(default="", description="Neo4j connection URI (bolt or neo4j+s)")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="", description="Neo4j password")

    # -- Database (Session / Report Persistence) --
    database_url: str = Field(
        default="sqlite+aiosqlite:///./interview_coach.db",
        description="SQLAlchemy async database URL. Use postgresql+asyncpg for production.",
    )

    # -- Embedding model --
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="sentence-transformers model name for vector embeddings",
    )

    # -- Application --
    app_name: str = "AI Interview Coach"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    # -- Interview defaults --
    max_questions: int = Field(default=10, description="Max questions per interview session")
    default_interview_type: str = Field(default="behavioral", description="Default interview type")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
