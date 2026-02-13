"""
Local embedding provider using sentence-transformers.

Wraps the configured model (default: all-MiniLM-L6-v2, 384-dim) and exposes
a simple encode() interface.  The model is loaded lazily on first use and
cached for the lifetime of the process.

On constrained hosts (Azure B1, 1.75 GB RAM) the initial load of PyTorch and
the transformer weights can take 30-60 seconds.  To avoid blocking the first
user request the Embedder exposes an ``is_ready`` property and a
``start_background_load`` helper so callers can skip vector search when the
model is not yet available and still serve the request with graph-only context.
"""

from __future__ import annotations

import logging
import threading
from functools import lru_cache

from backend.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Singleton-style wrapper around SentenceTransformer."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embedding_model
        self._model = None
        self._loading = False

    @property
    def is_ready(self) -> bool:
        """Return True when the underlying model is loaded and usable."""
        return self._model is not None

    def start_background_load(self) -> None:
        """Kick off model loading in a daemon thread (non-blocking)."""
        if self._model is not None or self._loading:
            return
        self._loading = True

        def _load_thread():
            try:
                self._load()
            except Exception:
                logger.exception("Background embedding model load failed")
            finally:
                self._loading = False

        t = threading.Thread(target=_load_thread, daemon=True)
        t.start()
        logger.info("Embedding model loading in background thread")

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info(
                "Embedding model loaded (dim=%d)",
                self._model.get_sentence_embedding_dimension(),
            )

    def encode(self, texts: str | list[str]) -> list[list[float]]:
        """
        Encode one or more texts into embedding vectors.

        Args:
            texts: A single string or list of strings.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        self._load()
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def encode_single(self, text: str) -> list[float]:
        """Encode a single text and return its embedding vector."""
        return self.encode(text)[0]

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding model."""
        self._load()
        return self._model.get_sentence_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Return the cached Embedder singleton."""
    return Embedder()
