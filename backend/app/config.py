import os
from pathlib import Path
from dotenv import load_dotenv

# config.py → app → backend → freshkart-support (root)
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Check the .env file in the project root folder.")

# Shared LLM settings used by all agents
LLM_CONFIG = {
    "config_list": [
        {
            "model": OPENAI_MODEL,
            "api_key": OPENAI_API_KEY,
            "api_type": "openai",
        }
    ],
    "temperature": 0.2,
    "cache_seed": None,
}