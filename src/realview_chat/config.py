from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

OUT_DIR = PROJECT_ROOT / "out"
FEEDBACK_PATH = OUT_DIR / "feedback.json"
GROUND_TRUTH_DIR = OUT_DIR / "ground_truth"
CASES_ROOT = PROJECT_ROOT / "cases"


def init_config():
    OUT_DIR.mkdir(exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(exist_ok=True)

@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    openai_model: str
    requests_per_minute: int
    max_retries: int
    retry_backoff_seconds: float

class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{PROJECT_ROOT / 'realview_chat.db'}"
    )

settings = Settings()

def load_config() -> AppConfig:
    load_dotenv(override=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    return AppConfig(
        openai_api_key=api_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "60")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_backoff_seconds=float(os.getenv("RETRY_BACKOFF_SECONDS", "1.5")),
    )
