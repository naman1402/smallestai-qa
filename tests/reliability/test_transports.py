"""The same streaming concerns across transports: SSE and WebSocket (the two streaming paths), with HTTP as
the baseline for latency.

Contract (docs/reference/smallest-docs-2026-11-18/):
  models__text-to-speech__streaming.md   "First chunk arrives in ~100ms"; SSE frames `event: audio` +
                                         `data: {audio, done:false, status:"206"}`, terminator `done: true`
  models__text-to-speech__overview.md    "~200 ms time to first byte"
  api-reference__concurrency-and-limits.md  the 1-request limit "applies to every ... TTS endpoint (sync, SSE,
                                         WebSocket)"; extra requests get 429 / are rejected with an error
  synthesize-speech-sse reference         documented errors 400/401/500 (JSON), like the sync route
Skill (.agents/skills/text-to-speech/references/streaming.md): SSE "Final frame: data: {"done": true}", and
"feed the raw PCM to your audio pipeline", so a stream that stalls is heard as a gap.
"""

import asyncio
import statistics
import threading

import pytest

from smallest_qa.utils import live
from smallest_qa.waves import tts
from smallest_qa.waves.payloads import tts_body, ws_payload

RATE = 24000
BYTES_PER_S = RATE * 2  # 16-bit mono PCM
LATENCY_BUDGET_MS = 400  # 2x the documented ~200 ms TTFB
JITTER_BUFFER_MS = 150  # what a playback client typically buffers before starting
SHORT = "Your appointment is confirmed for Tuesday."
LONG = ("Thanks for calling. I have pulled up your account and I can see the order you placed last Tuesday. "
        "It left our warehouse this morning and the courier expects to deliver it on Friday before noon. "
        "If you are not home, they will leave a card with instructions to collect it from the nearest depot.")


def underrun(events: list[tuple[float, int]]) -> dict:
    """Play the stream from its first chunk (plus a jitter buffer) and find the worst moment: negative
    headroom means the player ran out of audio before the next chunk arrived (an audible gap)."""
    t0, have, worst, gaps = events[0][0], 0.0, None, []
    for i, (t, n) in enumerate(events):
        played = max(0.0, (t - t0 - JITTER_BUFFER_MS) / 1000)
        if i:
            headroom = have - played
            worst = headroom if worst is None else min(worst, headroom)
            gaps.append(t - events[i - 1][0])
        have += n / BYTES_PER_S
    return {"audio_s": round(have, 2), "chunks": len(events), "min_headroom_s": round(worst or 0, 3),
            "max_gap_ms": round(max(gaps or [0]), 1), "stream_s": round((events[-1][0] - t0) / 1000, 2)}


def _ws_timeline(text: str, label: str) -> list[tuple[float, int]]:
    async def go():
        async with live.live(label=label) as s:
            sent = await s.send(ws_payload(text=text, sample_rate=RATE))
            await s.wait_for(lambda f: f.get("status") == "complete", timeout=30, since=sent)
            return [(f["t"] - sent, f["data"]["audio_bytes"]) for f in s.chunks_after(sent)]
    return asyncio.run(go())


def test_time_to_first_audio_per_transport():
    """Five sequential samples per transport (no concurrency). HTTP: first body byte; SSE: first audio event;
    WebSocket: first chunk after the send. Median must be within budget; the table goes in the evidence."""
    samples: dict[str, list] = {"http": [], "sse": [], "ws": []}
    for i in range(5):
        h = tts.synthesize(tts_body(text=SHORT, output_format="pcm", sample_rate=RATE), label=f"ttfa-http-{i}")
        samples["http"].append(h.ttfb_ms if h.status == 200 else None)
        e = tts.synthesize_sse(tts_body(text=SHORT, output_format="pcm", sample_rate=RATE), label=f"ttfa-sse-{i}")
        samples["sse"].append(e.first_audio_ms if e.status == 200 else None)
        w = _ws_timeline(SHORT, f"ttfa-ws-{i}")
        samples["ws"].append(w[0][0] if w else None)
    table = {k: {"median_ms": statistics.median([x for x in v if x is not None] or [0]),
                 "max_ms": max([x for x in v if x is not None] or [0]), "samples": v} for k, v in samples.items()}
    failed = {k: v for k, v in samples.items() if None in v}
    slow = {k: t["median_ms"] for k, t in table.items() if k != "http" and t["median_ms"] > LATENCY_BUDGET_MS}
    assert not failed and not slow, f"failed={failed} over-budget medians={slow} | {table}"


@pytest.mark.parametrize("transport", ["sse", "ws"])
def test_stream_keeps_ahead_of_playback(transport):
    """~20 s of speech: once playback starts at the first chunk (+150 ms buffer), audio must keep arriving
    faster than it plays. Negative headroom is an audible gap for the listener."""
    if transport == "sse":
        res = tts.synthesize_sse(tts_body(text=LONG, output_format="pcm", sample_rate=RATE), label="underrun-sse")
        assert res.status == 200 and res.done_frame, f"{res.status} {res.error_body} done={res.done_frame}"
        events = res.audio_events
    else:
        events = _ws_timeline(LONG, "underrun-ws")
    assert events, "no audio"
    r = underrun(events)
    assert r["min_headroom_s"] >= 0 and r["audio_s"] > 10, f"{transport}: {r}"


def test_concurrent_sse_streams_complete_intact_or_fail_explicitly():
    """SSE next to SSE, then SSE next to WebSocket. Each stream must either finish intact (done:true terminator,
    plausible length) or fail explicitly (429/4xx before streaming, or an error event): never truncated."""
    def sse(label, out, i):
        out[i] = tts.synthesize_sse(tts_body(text=LONG, output_format="pcm", sample_rate=RATE), label=label)

    def verdict(res) -> str:
        if res.status != 200:
            return f"explicit {res.status}"
        secs = len(res.audio) / BYTES_PER_S
        return "intact" if res.done_frame and secs > 10 else f"TRUNCATED ({secs:.1f} s, done={bool(res.done_frame)})"

    out: list = [None, None]
    threads = [threading.Thread(target=sse, args=(f"sse-pair-{i}", out, i)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    pair = [verdict(r) for r in out]

    async def with_ws():
        async with live.live(label="sse-vs-ws") as s:
            sent = await s.send(ws_payload(text=LONG, sample_rate=RATE))
            await s.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent)
            res = await asyncio.to_thread(tts.synthesize_sse, tts_body(text=SHORT, output_format="pcm",
                                                                       sample_rate=RATE), label="sse-during-ws")
            done = await s.wait_for(lambda f: f.get("status") == "complete", timeout=30, since=sent)
            ws_secs = s.audio_bytes_after(sent) / BYTES_PER_S
            return res, ("intact" if done and ws_secs > 10 else f"TRUNCATED ws ({ws_secs:.1f} s)"), s.errors()

    sse_res, ws_verdict, ws_errors = asyncio.run(with_ws())
    sse_verdict = "intact" if sse_res.status == 200 and sse_res.done_frame else f"explicit {sse_res.status}"
    results = {"sse+sse": pair, "sse(during ws)": sse_verdict, "ws(during sse)": ws_verdict,
               "request_ids": [r.request_id for r in out] + [sse_res.request_id]}
    assert not any("TRUNCATED" in str(v) for v in results.values()) and not ws_errors, results


def test_sse_client_disconnect_then_next_stream_is_served():
    """A client closes the SSE stream after 3 audio events (page closed, network drop). The next request must
    stream normally right away."""
    gone = tts.synthesize_sse(tts_body(text=LONG, output_format="pcm", sample_rate=RATE), label="sse-disconnect",
                              stop_after=3)
    nxt = tts.synthesize_sse(tts_body(text=SHORT, output_format="pcm", sample_rate=RATE), label="sse-after-disconnect")
    assert gone.stopped_early, f"could not disconnect early: {gone.status} {gone.error_body}"
    assert nxt.status == 200 and nxt.done_frame and nxt.audio, f"next stream: {nxt.status} {nxt.error_body}"


@pytest.mark.parametrize("override", [{"voice_id": "qa_no_such_voice"}, {"text": "   "}], ids=["unknown_voice",
                                                                                                  "blank_text"])
def test_sse_bad_request_fails_before_streaming(override):
    """A client opening an SSE stream should learn about a bad request the same way as on REST: a 4xx with a
    JSON error, not a 200 event-stream that carries the error (or nothing) inside."""
    res = tts.synthesize_sse(tts_body(**{"text": SHORT, "output_format": "pcm", "sample_rate": RATE, **override}),
                             label="sse-bad-request")
    ctype = res.headers.get("content-type", "")
    assert 400 <= (res.status or 0) < 500, f"status {res.status} ctype={ctype} frames={res.frames[:3]}"
    assert "json" in ctype and res.error_body, f"error not JSON: ctype={ctype} body={res.error_body!r}"
