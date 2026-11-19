"""Control run: the support agent with a stock Pro voice instead of the brand clone.

Question: are the clone runs' barge-in talk-over (R1), early mid-turn stalls and first-audio times properties of
the speech engine and its streaming, or of cloned voices? Only the voice changes: the journeys are the clone
suite's own functions (tests/e2e/test_support_agent.py), called with a `VoiceProfile("meher",
"lightning_v3.1_pro")` (Indian English + Hindi Pro voice, docs voices-languages), the same scripted replies,
thresholds and brand dictionary. Results go side by side with clone runs b3ede2aa, f0d2f3cf and 53d78cbd.

Changes from the clone suite, each to stay within one run's budget or to raise the sample:
  - the web call runs 3 times (15 turns, 3 barge-ins instead of 5 and 1); caller STT is live on the first call
    and replayed after (also on the phone call); busy hour keeps live STT, its 429 check depends on it
  - no onboarding, dictionary change or offboarding (they test cloning and dictionaries, not the voice)
  - no network drop: reconnect time is socket setup plus first audio, which every other turn already measures
  - a stall census over every turn's socket timeline (census.py), and a comparison table
"""

import json

import pytest
from e2e import test_support_agent as clone_suite
from e2e.conftest import assert_journey

from smallest_qa.app.scorecard import Scorecard
from smallest_qa.config import ROOT, settings
from smallest_qa.utils import evidence
from smallest_qa.utils.evidence import RUN_ID

from . import census
from .conftest import OUT

pytestmark = pytest.mark.clone  # the caller's side is cut from the owner's recording (--sample)

CLONE_RUNS = ["b3ede2aa", "f0d2f3cf", "53d78cbd"]  # 2026-11-19, GO WITH WORKAROUNDS 3/3


@pytest.mark.parametrize("call", [1, 2, 3])
def test_01_web_call_with_barge_in(call, state, scorecard, caller_clips, replay_stt, monkeypatch):
    """The clone suite's web call (3 turns, barge-in, one more turn), stock voice. Each call is scored on its
    own and its checks join the session scorecard, so one bad call does not fail the others."""
    monkeypatch.setattr(clone_suite, "_stt", replay_stt)
    monkeypatch.setattr(clone_suite, "RUN_ID", f"{RUN_ID}-c{call}")  # context ids distinct per call
    card = Scorecard()
    try:
        clone_suite.test_02_web_call_with_barge_in(state, card, caller_clips)
    finally:
        scorecard.checks += card.checks


def test_02_phone_call(state, scorecard, caller_clips, replay_stt, monkeypatch):
    """The clone suite's phone call (8 kHz, mu-law, carrier pacing), stock voice, caller STT replayed."""
    monkeypatch.setattr(clone_suite, "_stt", replay_stt)
    clone_suite.test_03_phone_call(state, scorecard, caller_clips)


def test_03_busy_hour(state, scorecard, caller_clips):
    """The clone suite's busy hour (3 concurrent callers, live STT), stock voice. Needs QA_MAX_IN_FLIGHT=4."""
    clone_suite.test_04_busy_hour(state, scorecard, caller_clips)


def test_04_stall_census_and_comparison(state, scorecard):
    """Every turn this run made, read back from its socket timelines: worst gap in the first 1.5 s of audio
    with the text already sent. Then the stock run beside the clone runs (out/e2e/<run>-stock/comparison.md)."""
    j = "stall census"
    rows = census.evidence_census(settings.evidence_dir, [RUN_ID])[RUN_ID]
    if not rows:
        pytest.skip("no socket timelines from this run in the evidence log")
    s = census.summarize(rows)
    evidence.log(label="e2e-stock-census", event="stall_census", rows=rows, summary=s)
    per_turn = ", ".join(f"{r['worst_gap_ms']:.0f}{'*' if r['text_sent'] else ''}" for r in rows)
    scorecard.check(j, f"turns with a > {census.STALL_MS} ms stall early in the turn (text already sent)",
                    f"{s['stalls']}/{s['turns']}", s["stalls"] == 0, "0 turns",
                    workaround="a longer jitter buffer (~600 ms), at the cost of response latency",
                    note=f"worst gap per turn in ms (* = text in hand): {per_turn}")

    clones = {}
    for run in CLONE_RUNS:
        path = ROOT / "out" / "e2e" / run / "scorecard.json"
        clones[run] = json.loads(path.read_text()) if path.is_file() else None
    found = [r for r in CLONE_RUNS if clones[r]]
    clone_rows = census.evidence_census(ROOT / "evidence", found) if found else {}
    stock = {"verdict": scorecard.verdict(), "score": scorecard.score(),
             "checks": [{"journey": c.journey, "name": c.name, "value": c.value} for c in scorecard.checks]}
    note = (f"Stock voice `{state['profile'].voice_id}` on `{state['profile'].model}`, brand dictionary "
            f"{'used' if state['profile'].dict_ids else 'NOT used'}. "
            "Clone runs without a scorecard in out/e2e are left out.")
    md = census.comparison_md(RUN_ID, stock, {r: clones[r] for r in found}, {RUN_ID: rows, **clone_rows}, note)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "comparison.md").write_text(md)
    print("\n" + md)
    assert_journey(scorecard, j)
