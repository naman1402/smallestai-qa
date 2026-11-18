"""The voice-agent turn loop over the TTS WebSocket: what Smallest's customers actually build.

An agent streams LLM text in as it arrives, plays audio as soon as possible, stops when the caller
interrupts (barge-in), and keeps the socket alive while the caller thinks. Docs this is checked against
(docs/reference/smallest-docs-2026-11-18/):
  models__text-to-speech__streaming.md       "First chunk arrives in ~100ms"
  models__text-to-speech__overview.md        "~200 ms time to first byte"
  models__text-to-speech__continuations.md   context_id fragments; complete is not terminal inside a context;
                                             "cancel_request: true discards whatever is currently buffered ...
                                             does not end the context itself" (cancel_request is on no
                                             reference page: it is missing from the WebSocket message schema)
  api-reference__models__text-to-speech__tts.md  ping -> pong resets the idle timer; complete_backoff_ms 4000
  api-reference__concurrency-and-limits.md   1 TTS request per account across all transports
Skill (.agents/skills/text-to-speech/references/streaming.md) shows only a one-shot request that `break`s on
`complete`: no context_id, no cancel, no keep-alive, and the retiring default model.
"""

import asyncio

from smallest_qa.utils import live
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves.payloads import PRO_MODEL, PRO_VOICE, ws_payload

LATENCY_BUDGET_MS = 400  # 2x the documented ~200 ms TTFB (the streaming page claims ~100 ms)
CHUNK_BYTES_PER_S = 24000 * 2  # 16-bit mono at the default payload rate

TURNS = [  # LLM-style replies: the first fragment is a full sentence so it can be released at once
    ["Sure, I can help with that.", " Your order shipped this morning", " and should arrive by Friday."],
    ["Of course.", " I have moved your delivery", " to Saturday between nine and noon."],
    ["Got it.", " Is there anything else", " I can help you with today?"],
]


def fragment(cid: str, text: str, more: bool = True) -> dict:
    return ws_payload(text=text, context_id=cid, **{"continue": more})


def close_context(cid: str) -> dict:
    return {"context_id": cid, "voice_id": PRO_VOICE, "model": PRO_MODEL, "continue": False}


async def stream_reply(s: live.LiveSocket, cid: str, parts: list[str], gap: float = 0.08) -> tuple[float, float]:
    """Send a reply as LLM-like fragments; returns (first send, closing send) times."""
    first = await s.send(fragment(cid, parts[0]))
    for part in parts[1:]:
        await asyncio.sleep(gap)
        await s.send(fragment(cid, part))
    end = await s.send(close_context(cid))
    return first, end


def test_multi_turn_conversation_on_one_socket():
    """Three turns, one socket, think time between turns. Per turn: time to first audio, audio produced, the
    socket stays open (complete is not terminal inside a context)."""
    async def go():
        async with live.live(label="agent-turns") as s:
            turns = []
            for n, parts in enumerate(TURNS):
                cid = f"qa-turn{n}-{RUN_ID}"
                first, end = await stream_reply(s, cid, parts)
                done = await s.wait_for(lambda f: f.get("status") == "complete", timeout=15, since=end)
                turns.append({"turn": n, "ttfa_ms": s.first_chunk_ms(first), "complete": bool(done),
                              "audio_bytes": s.audio_bytes_after(first), "closed_at": s.closed_at})
                await asyncio.sleep(1.5)  # caller speaks / thinks
            return turns, s.errors(), s.closed_at

    turns, errors, closed_at = asyncio.run(go())
    problems = [f"turn {t['turn']}: no audio" for t in turns if not t["audio_bytes"]]
    problems += [f"turn {t['turn']}: socket closed at {t['closed_at']} ms" for t in turns if t["closed_at"]]
    slow = [t for t in turns if t["ttfa_ms"] is None or t["ttfa_ms"] > LATENCY_BUDGET_MS]
    if slow:
        problems.append(f"time to first audio over {LATENCY_BUDGET_MS} ms: {[t['ttfa_ms'] for t in slow]}")
    assert not errors and not problems, f"{problems} | errors={errors} | turns={turns} | closed_at={closed_at}"


def test_barge_in_cancel_stops_audio_and_context_continues():
    """Caller interrupts mid-reply. Docs promise only that cancel_request "discards whatever is currently buffered";
    an agent needs speech to stop. Checks both: (1) text still buffered (no sentence end yet) is never spoken,
    (2) audio of already-released sentences stops within ~0.5 s of the cancel, and (3) the context accepts the
    next reply. Verified 2026-11-18: (1) holds; (2) does not - segments that start generating after the cancel
    are still streamed in full."""
    long_reply = ("Let me walk you through the full refund policy. Refunds are processed within five business "
                  "days. Items must be unused and in their original packaging. Shipping costs are not refunded "
                  "unless the item arrived damaged. You can start a return from the orders page at any time.")
    cid = f"qa-bargein-{RUN_ID}"

    async def go():
        async with live.live(label="agent-barge-in") as s:
            sent = await s.send(fragment(cid, long_reply))
            await s.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent)
            buffered = await s.send(fragment(cid, " And one more thing about your order number"))  # no sentence end
            await asyncio.sleep(0.4)  # caller starts talking ~0.4 s into playback
            cancel_at = await s.send({"context_id": cid, "cancel_request": True})
            await s.quiet(4.5, since=cancel_at, timeout=25)  # past max_buffer_delay_ms (3000)
            after_cancel = s.chunks_after(cancel_at)
            segments = {}
            for f in after_cancel:
                segments.setdefault(f.get("request_id"), f["t"])
            started_after = {rid: round(t - cancel_at, 1) for rid, t in segments.items()
                             if not any(c["t"] < cancel_at and c.get("request_id") == rid for c in s.frames)}
            resume = await s.send(fragment(cid, "Sorry, go ahead.", more=False))
            resumed = await s.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=resume)
            return {"buffered_at": buffered, "cancel_at": cancel_at,
                    "audio_s_after_cancel": round(s.audio_bytes_after(cancel_at) / CHUNK_BYTES_PER_S, 2),
                    "late_chunks": len([f for f in after_cancel if f["t"] - cancel_at > 500]),
                    "segments_started_after_cancel_ms": started_after,
                    "frames_after_cancel": [f for f in s.after(cancel_at) if f.get("status") != "chunk"][:5],
                    "resumed": bool(resumed), "errors": s.errors()}

    r = asyncio.run(go())
    problems = []
    if r["late_chunks"]:
        problems.append(f"speech kept streaming after cancel: {r['audio_s_after_cancel']} s of audio, "
                        f"segments that started after the cancel: {r['segments_started_after_cancel_ms']}")
    if not r["resumed"]:
        problems.append("context did not accept a new reply after cancel")
    assert not problems and not r["errors"], f"{problems} | {r}"


def test_one_shot_complete_backoff_does_not_block_the_next_turn():
    """Agents built from the doc samples send one-shot requests and wait for `complete` (default 4000 ms after
    the last chunk). If that wait also holds the account's single concurrency slot, the next turn - on any
    socket - is rejected for ~4 s after the audio has finished."""
    async def go():
        async with live.live(label="backoff-turn-A") as a, live.live(label="backoff-turn-B") as b:
            sent_a = await a.send(ws_payload(text="Your order has shipped."))
            await a.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent_a)
            last = await a.quiet(0.5, since=sent_a)  # audio finished, complete not yet sent
            sent_b = await b.send(ws_payload(text="Anything else I can help with?"))
            got_b = await b.wait_for(lambda f: f.get("status") in ("chunk", "error") or "error" in f, timeout=10,
                                     since=sent_b)
            done_a = await a.wait_for(lambda f: f.get("status") == "complete", timeout=10, since=sent_a)
            return {"a_last_chunk": last, "a_complete": done_a and done_a["t"], "b_sent": sent_b,
                    "b_first": got_b, "b_ttfa_ms": b.first_chunk_ms(sent_b)}

    r = asyncio.run(go())
    first = r["b_first"] or {}
    assert first.get("status") == "chunk", f"turn B during A's complete backoff: {first or 'nothing in 10 s'} | {r}"


def test_keepalive_ping_bridges_caller_think_time():
    """A client pinging every 2 s (as a real agent does, independent of turns) must keep a 5 s-timeout socket open
    through a turn and 12 s of caller silence, every ping answered with pong, and the next turn still served.
    Note: the idle timer counts only client messages, so a client that stops sending while the server still owes
    `complete` (~4 s after the last chunk) is closed mid-turn at short timeouts."""
    async def go():
        async with live.live(query="timeout=5", label="agent-keepalive") as s:
            pongs: list = []

            async def pinger():
                while True:
                    await asyncio.sleep(2)
                    t = await s.ping()
                    pong = await s.wait_for(lambda f: f.get("type") == "pong", timeout=1.5, since=t)
                    pongs.append(round(pong["t"] - t, 1) if pong else None)

            task = asyncio.create_task(pinger())
            cid = f"qa-think-{RUN_ID}"
            first, end = await stream_reply(s, cid, TURNS[0])
            done = await s.wait_for(lambda f: f.get("status") == "complete", timeout=15, since=end)
            await asyncio.sleep(12)  # caller silence, longer than the 5 s timeout
            second = await s.send(fragment(cid + "-2", "Thanks for waiting.", more=False))
            served = await s.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=second)
            task.cancel()
            return {"turn1_complete": bool(done), "pong_ms": pongs, "served": bool(served),
                    "closed_at": s.closed_at, "close": (s.close_code, s.close_reason), "errors": s.errors()}

    r = asyncio.run(go())
    ok = r["turn1_complete"] and r["served"] and r["closed_at"] is None and None not in r["pong_ms"]
    assert ok, r
