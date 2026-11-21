"""Claims in Smallest's official agent skill that the API reference contradicts.

Coding agents (Claude Code, Codex, Cursor) write customer integrations from this skill, so a wrong
claim ships straight into customer code. Source: .agents/skills/text-to-speech (smallest-inc/skills,
installed 2026-11-18) against docs/reference/smallest-docs-2026-11-18/. Each test asserts the
API reference; a failure means the skill is right and the reference is wrong (still a finding).

Skill claims checked elsewhere: "Pro is English+Hindi only" (test_voices languages) and
"cloning is lightning_v3.1 only, not Pro" (tests/cloning pro pool). Findings: evidence/2026-11-18-tts-findings.md (F3).
"""

import pytest

from smallest_qa.utils import audio
from smallest_qa.waves import tts, voices
from smallest_qa.waves.payloads import V31_VOICE, tts_body

TEXT = "The quick brown fox jumps over the lazy dog near the quiet river bank."


@pytest.mark.parametrize("fmt", ["ulaw", "alaw"])
def test_telephony_formats_the_skill_advertises(fmt):
    """Skill and API reference both list output_format pcm | mp3 | wav | ulaw | alaw (synthesize-speech enum).
    G.711 at 8 kHz is what phone bridges need; this checks REST actually serves it."""
    ex = tts.synthesize(tts_body(text=TEXT, output_format=fmt, sample_rate=8000), label=f"skill-{fmt}")
    if ex.status == 400:
        pytest.fail(f"skill advertises {fmt} but the API rejects it: {ex}")
    assert ex.status == 200, ex
    seconds = len(ex.body) / 8000  # G.711: one byte per sample
    assert ex.audio_format is None and 2.0 <= seconds <= 9.0, f"{fmt}: {seconds:.2f} s if 8-bit G.711 | {ex}"


def test_accept_header_does_not_change_the_response():
    """Skill: "Always set Accept: audio/wav; omitting it can return an empty or unplayable response."
    Reference: "The server ignores it; output_format sets the audio format." """
    with_accept = tts.synthesize(tts_body(text=TEXT), headers={"Accept": "audio/wav"}, label="skill-accept-wav")
    without = tts.synthesize(tts_body(text=TEXT), headers={"Accept": None}, label="skill-no-accept")
    assert with_accept.status == without.status == 200, f"{with_accept} | {without}"
    d = (audio.duration(with_accept.body, 24000), audio.duration(without.body, 24000))
    assert without.audio_format == "wav" and d[1] and d[1] > 1.0, f"no Accept header -> {without} ({d[1]} s)"


def test_voice_catalog_is_scoped_per_pool():
    """Skill: GET /lightning-v3.1/get_voices returns "the union of standard and Pro catalogs".
    Reference: "pool-scoped: /lightning-v3.1/get_voices returns Standard voices only"."""
    std, pro = voices.list_voices("lightning-v3.1"), voices.list_voices("lightning-v3.1-pro")
    assert std.status == pro.status == 200, f"{std} | {pro}"
    std_ids, pro_ids = set(voices.voice_ids(std)), set(voices.voice_ids(pro))
    assert pro_ids and not pro_ids <= std_ids, (
        f"every Pro voice ({len(pro_ids)}) is in the Standard list ({len(std_ids)}): skill right, reference wrong")


def test_mismatched_voice_and_model_is_rejected():
    """Skill: mismatched pairs "are not rejected" and can return wrong audio. Reference: a mismatched pair
    returns 400 (Voice '<id>' is not available on the lightning_v3.1_pro model)."""
    ex = tts.synthesize(tts_body(text=TEXT, voice_id=V31_VOICE), label="skill-mismatch")  # standard voice, Pro model
    assert ex.status == 400, f"standard voice on the Pro model: {ex} wav={audio.wav_info(ex.body)}"
