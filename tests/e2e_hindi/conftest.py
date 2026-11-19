"""Fixtures for the Hindi support-agent journeys: their own scorecard and state, and a synthetic Hindi caller.

Run in order: `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_hindi -v -s`.
The scorecard is written to out/e2e/<run id>-hindi/scorecard.md; the clone to delete by hand is printed at the end.

The caller: the owner's recording is English, so Hindi caller turns are synthesized once per run with a stock
Hindi Pro voice (llm_hi.CALLER_VOICE) over REST, 16 kHz WAV, and transcribed by Pulse with language=hi like a
real caller. A synthetic voice is cleaner than a phone caller, so caller-side STT results are a best case.
"""

import pytest
from e2e.conftest import require_profile, sample  # noqa: F401  (sample: fixture, skips without it/ffmpeg)

from smallest_qa.app import llm_hi
from smallest_qa.app.scorecard import Scorecard
from smallest_qa.config import ROOT
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import pronunciation, tts
from smallest_qa.waves.payloads import PRO_MODEL, tts_body


@pytest.fixture(scope="session")
def state() -> dict:
    """'profile' (VoiceProfile), 'dict_id', 'brand_says' (respelling in effect), 'danda_fix', 'clone_ids'."""
    s = {"clone_ids": []}
    yield s
    if s.get("dict_id"):
        pronunciation.delete(s["dict_id"])  # dictionaries can be deleted; clones cannot (C1)


@pytest.fixture(scope="session")
def scorecard(state):
    card = Scorecard()
    yield card
    if card.checks:
        path = card.write(ROOT / "out" / "e2e" / f"{RUN_ID}-hindi")
        print(f"\nscorecard: {path}  verdict: {card.verdict()} ({card.score()}%)")
    if state["clone_ids"]:
        print(f"clones to delete in the dashboard: {state['clone_ids']}")


@pytest.fixture(scope="session")
def hindi_callers(state) -> list[tuple[str, bytes]]:
    """(what the caller says, 16 kHz WAV of it), one per caller turn. Not synthesized if onboarding failed."""
    require_profile(state)
    out = []
    for n, text in enumerate(llm_hi.CALLER):
        ex = tts.synthesize(tts_body(text=text, voice_id=llm_hi.CALLER_VOICE, model=PRO_MODEL, language="hi",
                                     sample_rate=16000, output_format="wav"), label=f"e2e-hi-caller-{n}")
        assert ex.status == 200, ex
        out.append((text, ex.body))
    return out
