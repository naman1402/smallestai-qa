"""Instant clone, end to end, the way a customer uses it: create -> listed -> speak on every transport ->
wrong model fails loudly -> delete -> gone.

Contract: docs/reference/smallest-docs-2026-11-18/models__voice-cloning__instant-clone-api.md
  - model defaults to lightning-v3.1 (retiring 2026-11-30; "clones made on lightning-v3.1 will stop working")
  - list returns modelIds; "pair the resulting voice_id with the matching TTS model"
  - a mismatched pair returns 400; docs warn of ~100-200 byte "empty" WAVs on a wrong pool
  - delete: DELETE /waves/v1/lightning-large {"voiceId"}
"""

import asyncio

import pytest

from smallest_qa.utils import audio
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import cloning, tts
from smallest_qa.waves.payloads import DROP, PRO_MODEL, V31_MODEL, tts_body, ws_payload

pytestmark = pytest.mark.clone

TEXT = "This is my cloned voice speaking."
# pool -> (create fields, listed modelId, matching TTS model, other TTS model)
POOLS = {
    "default": ({}, "lightning-v3.1", V31_MODEL, PRO_MODEL),
    "pro": ({"model": "lightning-v3.1-pro"}, "lightning-v3.1-pro", PRO_MODEL, V31_MODEL),
}


@pytest.mark.parametrize("pool", list(POOLS))
def test_clone_lifecycle(pool, variant):
    fields, model_id, model, other = POOLS[pool]
    sample = variant("ok.wav", "-ac", "1", "-ar", "24000", "-t", "12")
    created = cloning.create(sample, name=f"qa-{pool}-{RUN_ID}", language="en", **fields)
    vid = cloning.voice_id(created)
    assert created.status == 200 and vid, created
    try:
        entry = cloning.find(cloning.list_clones(), vid)
        assert entry and model_id in (entry.get("modelIds") or []), f"list entry: {entry}"

        rest = tts.synthesize(tts_body(voice_id=vid, model=model, text=TEXT, output_format="pcm"), label="clone-rest")
        sse = tts.synthesize_sse(tts_body(voice_id=vid, model=model, text=TEXT, output_format="pcm"), label="clone-sse")
        sock = asyncio.run(tts.synthesize_ws(ws_payload(voice_id=vid, model=model, text=TEXT), label="clone-ws"))
        seconds = {k: audio.pcm_duration(len(v), 24000)
                   for k, v in {"rest": rest.body if rest.status == 200 else b"", "sse": sse.audio,
                                "ws": sock.audio}.items()}
        assert all(v > 0.8 for v in seconds.values()), (
            f"clone audio seconds={seconds} | rest={rest} | sse={sse.status} {sse.error_body} | ws={sock.error_frames}")

        wrong = tts.synthesize(tts_body(voice_id=vid, model=other, text=TEXT), label="clone-wrong-pool")
        assert wrong.status == 400, f"clone on the wrong pool: {wrong} wav={audio.wav_info(wrong.body)}"
    finally:
        deleted = cloning.delete(vid)
    assert deleted.status == 200, deleted
    assert cloning.find(cloning.list_clones(), vid) is None, "deleted clone still listed"
    after = tts.synthesize(tts_body(voice_id=vid, model=DROP, text=TEXT), label="clone-after-delete")
    assert 400 <= after.status < 500, f"deleted clone still speaks: {after}"
