"""
Central config. Nothing else in the codebase should call os.environ or
open a YAML file directly — everything routes through this module so
there's one place to change if a config source ever moves.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings:
    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'ai_tech_radar.db'}"
    )

    # --- Collector credentials ---
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN") or None
    REDDIT_CLIENT_ID: str | None = os.getenv("REDDIT_CLIENT_ID") or None
    REDDIT_CLIENT_SECRET: str | None = os.getenv("REDDIT_CLIENT_SECRET") or None
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "ai-tech-radar/0.1")
    SEMANTIC_SCHOLAR_API_KEY: str | None = (
        os.getenv("SEMANTIC_SCHOLAR_API_KEY") or None
    )

    # --- LLM summarization ---
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or None
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY") or None
    LLM_DAILY_SUMMARY_CAP: int = int(os.getenv("LLM_DAILY_SUMMARY_CAP", "10"))

    # --- Relevance scoring weights (architecture doc §2.6) ---
    RELEVANCE_WEIGHTS = {
        "topic_match": 0.35,
        "source_quality": 0.20,
        "recency": 0.20,
        "popularity": 0.15,
        "coverage_breadth": 0.10,
    }

    # --- Dedup ---
    DEDUP_SIMILARITY_THRESHOLD: float = 0.85
    DEDUP_CLASSIFICATION_FALLBACK_THRESHOLD: float = 0.40


settings = Settings()


def load_sources_config() -> dict:
    """RSS feeds + official-company source list (architecture doc §2.11)."""
    path = CONFIG_DIR / "sources.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_categories_config() -> dict:
    """The 8 categories + their keyword rules (architecture doc §2.5)."""
    path = CONFIG_DIR / "categories.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
