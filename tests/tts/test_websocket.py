"""Lightning TTS over WebSocket: wss://api.smallest.ai/waves/v1/tts/live, one request per socket.

Contract: docs/reference/smallest-docs-2026-11-18/api-reference__models__text-to-speech__tts.md (asyncapi)
and models__text-to-speech__streaming.md:
  - frames {session_id, request_id, status: chunk|word_timestamp|complete, data}
  - `complete` is terminal for a one-shot request: "the server closes the WebSocket after this"
  - complete_backoff_ms: "time to wait after the last chunk is sent before sending the complete response.
    Default is 4000ms."
"""

import asyncio
import json

from smallest_qa.utils import audio, ws
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import tts
from smallest_qa.waves.payloads import PRO_MODEL, PRO_VOICE, ws_payload


def test_one_shot_request_waits_for_complete_backoff():
    """Documented default complete_backoff_ms is 4000: every one-shot request ends ~4 s after its last audio
    chunk, and doc samples wait for `complete`. Measures that wait with the default and with 0."""
    gaps = {}
    for backoff in (None, 0):
        extra = {} if backoff is None else {"complete_backoff_ms": backoff}
        tl = asyncio.run(tts.synthesize_ws(ws_payload(**extra), label=f"tts-ws-backoff-{backoff}"))
        assert not tl.error_frames and tl.complete_after_last_chunk_ms is not None, tl.frames
        gaps["default" if backoff is None else "0"] = tl.complete_after_last_chunk_ms
    assert gaps["default"] <= 4000 + 1500 and gaps["0"] <= 1500, f"ms from last chunk to complete: {gaps}"


def test_word_timestamps_align_with_text_and_audio():
    """docs/.../models__text-to-speech__word-timestamps.md: one word_timestamp per input word, `id` 0-indexed,
    `word` verbatim from the input (un-normalized), start/end in seconds within the audio. This is what
    captions and lip sync are built on. Text and voice are the doc's own example."""
    text = "I bought 3 cats for $100 on Dec 25th"
    tl = asyncio.run(tts.synthesize_ws(ws_payload(text=text, voice_id="meher", word_timestamps=True),
                                       label="tts-ws-word-ts"))
    words = [f["data"] for f in tl.frames if f.get("status") == "word_timestamp"]
    assert words, f"no word_timestamp frames on a documented voice; frames={tl.frames[:5]}"
    seconds = audio.pcm_duration(len(tl.audio), 24000)
    expected = text.split()
    problems = []
    if [w.get("word") for w in words] != expected:
        problems.append(f"words {[w.get('word') for w in words]} != input {expected}")
    if [w.get("id") for w in words] != list(range(len(words))):
        problems.append(f"ids {[w.get('id') for w in words]}")
    if any(w["start"] >= w["end"] for w in words):
        problems.append("a word with start >= end")
    if any(b["start"] < a["start"] for a, b in zip(words, words[1:], strict=False)):
        problems.append("starts go backwards")
    if words[-1]["end"] > seconds + 0.25:
        problems.append(f"last word ends at {words[-1]['end']} s, audio is {seconds} s")
    assert not problems, f"{problems} | request_ids={tl.request_ids}"


def test_continuation_speaks_fragments_as_one_generation():
    """docs/.../models__text-to-speech__continuations.md: fragments sharing a context_id are buffered and spoken
    as one generation; fragments arriving close together "reliably collapse to a single release";
    session_id is stable. This is the LLM-token-streaming path a voice agent uses."""
    fragments = ["Thanks for calling. Your order ", "shipped this morning ", "and should arrive ", "by Friday."]
    cid = f"qa-ctx-{RUN_ID}"

    async def run():
        async with ws.connect(label="tts-ws-context") as sock:
            for frag in fragments:
                await sock.send(json.dumps(ws_payload(text=frag, context_id=cid, **{"continue": True})))
                await asyncio.sleep(0.2)
            await sock.send(json.dumps({"context_id": cid, "voice_id": PRO_VOICE, "model": PRO_MODEL,
                                        "continue": False}))
            return await ws.exchange(sock, None, label="tts-ws-context", idle=8.0, until_complete=False)

    tl = asyncio.run(run())
    one_shot = asyncio.run(tts.synthesize_ws(ws_payload(text="".join(fragments)), label="tts-ws-context-ref"))
    assert not tl.error_frames, tl.error_frames
    assert tl.audio, f"no audio for the context; frames={tl.frames}"
    sessions = {f.get("session_id") for f in tl.frames if f.get("session_id")}
    ratio = len(tl.audio) / max(len(one_shot.audio), 1)
    problems = []
    if len(sessions) != 1:
        problems.append(f"session_ids {sessions}")
    if len(tl.complete_ms) != 1:
        problems.append(f"{len(tl.complete_ms)} releases (complete frames), docs say fragments collapse to one")
    if not 0.75 <= ratio <= 1.3:
        problems.append(f"context audio is {ratio:.2f}x the one-shot audio of the same text (dropped/repeated?)")
    assert not problems, f"{problems} | request_ids={tl.request_ids}"
