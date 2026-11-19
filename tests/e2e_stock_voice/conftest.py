"""Fixtures for the stock-voice control run: the clone suite's fixtures and journeys, with a stock Pro voice.

Run: `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_stock_voice -v -s` (needs samples/my_voice.wav and ffmpeg for
the caller's side; no clone is made). Writes out/e2e/<run id>-stock/{scorecard,comparison}.md.
"""

import time

import pytest
from e2e import test_support_agent as clone_suite
from e2e.conftest import caller_clips, sample  # noqa: F401  (fixtures reused as-is)

from smallest_qa.app.llm import BRAND
from smallest_qa.app.profile import VoiceProfile
from smallest_qa.app.scorecard import Scorecard
from smallest_qa.config import ROOT
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import pronunciation
from smallest_qa.waves.payloads import PRO_MODEL, PRO_VOICE

OUT = ROOT / "out" / "e2e" / f"{RUN_ID}-stock"
live_stt = clone_suite._stt  # kept before any test patches the suite's STT


@pytest.fixture(scope="session")
def scorecard():
    card = Scorecard()
    yield card
    if card.checks:
        path = card.write(OUT)
        print(f"\nscorecard: {path}  verdict: {card.verdict()} ({card.score()}%)")


@pytest.fixture(scope="session")
def state():
    """The stock voice as the product's profile. The clone runs said the brand name through a dictionary, so the
    same one is created here (same text on both voices) and deleted at the end."""
    d = pronunciation.create([{"word": BRAND, "pronunciation": clone_suite.BRAND_SAYS}])
    dict_id = (d.json or {}).get("id") if isinstance(d.json, dict) else None
    if not dict_id:
        print(f"\nbrand dictionary not created ({d.status}); running without it: {d.request_id}")
    profile = VoiceProfile(voice_id=PRO_VOICE, model=PRO_MODEL, dict_ids=[dict_id] if dict_id else [])
    yield {"profile": profile, "dict_id": dict_id, "clone_ids": []}
    if dict_id:
        gone = pronunciation.delete(dict_id)
        print(f"\nbrand dictionary {dict_id} deleted: {gone.status}")


@pytest.fixture(scope="session")
def replay_stt():
    """Drop-in for the suite's `_stt`: each caller clip is transcribed live once, then replayed, sleeping the
    measured STT time so the call idles as it would. STT does not depend on the agent's voice."""
    cache = {}

    def stt(wav: bytes, label: str, language: str = "en"):
        if wav in cache:
            time.sleep((cache[wav][0].total_ms or 0) / 1000)
        else:
            cache[wav] = live_stt(wav, label, language)
        return cache[wav]

    return stt
