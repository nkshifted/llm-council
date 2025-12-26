"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of CLI model identifiers
COUNCIL_MODELS = [
    "gemini",
    "claude",
    "codex",
    "amp",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "gemini"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
