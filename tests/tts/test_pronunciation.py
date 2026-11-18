"""Pronunciation dictionaries: do they actually change the speech, everywhere, and fail loudly when stale?

Contract: docs/reference/smallest-docs-2026-11-18/models__text-to-speech__pronunciation-dictionaries.md
  "pronunciation_dicts works the same way across all three synthesis modes"
Audio is not transcribed: a made-up word respelled as a long phrase must make the audio clearly longer.
"""

import asyncio

from smallest_qa.utils import audio
from smallest_qa.waves import pronunciation, tts
from smallest_qa.waves.payloads import tts_body, ws_payload

WORD = "Qzvx"
TEXT = f"Please say {WORD} clearly."


def test_dictionary_applies_on_every_transport_and_stale_ids_fail():
    created = pronunciation.create([{"word": WORD, "pronunciation": "quality assurance verification experiment"}])
    did = (created.json or {}).get("id") if isinstance(created.json, dict) else None
    assert created.status == 200 and did, created
    try:
        dicts = [did]
        plain = tts.synthesize(tts_body(text=TEXT, output_format="pcm"), label="dict-off")
        rest = tts.synthesize(tts_body(text=TEXT, output_format="pcm", pronunciation_dicts=dicts), label="dict-rest")
        sse = tts.synthesize_sse(tts_body(text=TEXT, output_format="pcm", pronunciation_dicts=dicts), label="dict-sse")
        sock = asyncio.run(tts.synthesize_ws(ws_payload(text=TEXT, pronunciation_dicts=dicts), label="dict-ws"))
        assert plain.status == rest.status == sse.status == 200 and sock.audio, f"{plain} | {rest} | {sse.error_body}"
        s = {k: audio.pcm_duration(len(v), 24000)
             for k, v in {"off": plain.body, "rest": rest.body, "sse": sse.audio, "ws": sock.audio}.items()}
        # the respelling adds ~4 spoken words (~1 s); under +0.5 s means the dictionary was ignored
        ignored = [k for k in ("rest", "sse", "ws") if s[k] < s["off"] + 0.5]
        assert not ignored, f"dictionary had no effect on {ignored}; seconds={s}"
    finally:
        deleted = pronunciation.delete(did)
    assert deleted.status == 200, deleted
    # a deleted or mistyped dictionary ID that is silently ignored means wrong brand names in production, unnoticed
    stale = tts.synthesize(tts_body(text=TEXT, pronunciation_dicts=[did]), label="dict-stale")
    assert 400 <= stale.status < 500, f"TTS with a deleted dictionary ID was accepted: {stale}"
