"""Fixtures for the support-agent journeys: one shared scorecard, one shared state (the voice profile made
during onboarding), and caller utterances cut from the owner's own recording.

Run the whole file in order: `.venv/bin/pytest tests/e2e -v` (busy hour needs QA_MAX_IN_FLIGHT=4).
The scorecard is written to out/e2e/<run id>/scorecard.md at the end of the session.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from smallest_qa.app.scorecard import Scorecard
from smallest_qa.config import ROOT
from smallest_qa.utils.evidence import RUN_ID

CALLER_CUTS = [(1.5, 3.5), (5.0, 4.0), (9.0, 4.0)]  # (start s, length s) of the owner's recording


@pytest.fixture(scope="session")
def scorecard():
    card = Scorecard()
    yield card
    if card.checks:
        path = card.write(ROOT / "out" / "e2e" / RUN_ID)
        print(f"\nscorecard: {path}  verdict: {card.verdict()} ({card.score()}%)")


@pytest.fixture(scope="session")
def state() -> dict:
    """Shared across journeys: 'profile' (VoiceProfile), 'dict_id', 'clone_ids' (to delete by hand)."""
    return {"clone_ids": []}


@pytest.fixture(scope="session")
def sample(pytestconfig) -> Path:
    path = Path(pytestconfig.getoption("--sample"))  # option defined in tests/conftest.py
    if not path.is_file():
        pytest.skip(f"no voice sample at {path}")
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    return path


@pytest.fixture(scope="session")
def caller_clips(sample, tmp_path_factory) -> list[bytes]:
    """The 'caller' speaking: three 16 kHz mono WAV utterances cut from the owner's own recording."""
    out = tmp_path_factory.mktemp("caller")
    clips = []
    for i, (start, length) in enumerate(CALLER_CUTS):
        f = out / f"caller_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(length), "-i", str(sample),
                        "-ac", "1", "-ar", "16000", str(f)], check=True)
        clips.append(f.read_bytes())
    return clips


def require_profile(state):
    if "profile" not in state:
        pytest.skip("onboarding did not produce a voice profile")
    return state["profile"]


def assert_journey(card: Scorecard, journey: str):
    """A journey fails only on checks that failed with no workaround; workarounds are scored, not failed."""
    hard = [c for c in card.failed(journey) if not c.workaround]
    assert not hard, "\n".join(f"{c.name}: {c.value} (threshold {c.threshold}) {c.evidence[:2]}" for c in hard)
