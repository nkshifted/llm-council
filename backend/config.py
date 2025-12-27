"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key (kept for potential future use)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter API endpoint (kept for potential future use)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Note: COUNCIL_MODELS and CHAIRMAN_MODEL are now managed dynamically
# through cli_config.py and stored in data/cli_config.json

# Data directory for conversation storage
DATA_DIR = "data/conversations"
