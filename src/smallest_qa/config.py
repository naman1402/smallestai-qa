"""Runtime settings, read once from the environment and the repo's .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    evidence_dir: Path
    max_in_flight: int  # brief: "at most about five requests at once"

    @property
    def ws_url(self) -> str:
        return "wss://" + self.base_url.split("://", 1)[1]


def load() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        api_key=os.environ.get("SMALLEST_API_KEY", "").strip(),
        base_url=os.environ.get("SMALLEST_BASE_URL", "https://api.smallest.ai").rstrip("/"),
        evidence_dir=Path(os.environ.get("QA_EVIDENCE_DIR", ROOT / "evidence")),
        max_in_flight=min(int(os.environ.get("QA_MAX_IN_FLIGHT", "3")), 5),
    )


settings = load()
