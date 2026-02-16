#!/usr/bin/env bash
# Azure App Service startup script for the AI Interview Coach backend.
# Runs gunicorn with uvicorn workers for async support.
# The 120s timeout accommodates the STT -> LLM -> TTS pipeline.

gunicorn backend.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --workers 2
