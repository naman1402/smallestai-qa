"""Concurrency and rate limits, kept inside the brief's cap (at most 5 requests or sockets at once).

Contract: docs/reference/smallest-docs-2026-11-18/api-reference__concurrency-and-limits.md
  "Only 1 Text-to-Speech request can be actively processed at a time per account"; it "applies to every
   Lightning v3.1 TTS endpoint (sync, SSE, WebSocket)"; a second HTTP request gets "429 Too Many Requests";
  "up to 5 WebSocket connections ... Additional requests ... will be rejected with an error";
  "approximately 4x your concurrency limit in parallel conversations ... handle 429 errors gracefully".
models__troubleshooting__error-reference.md: back off from 500 ms doubling to 30 s, respect Retry-After.
models__text-to-speech__sync-async.md: the "Asynchronous" sample fires 3 requests with asyncio.gather and
writes each body to .wav without checking the status.
Skill (.agents/skills/text-to-speech/SKILL.md): "429 Rate limited: back off and retry", no Retry-After, and no
mention of the 1-request limit.
"""

import asyncio
import threading

import pytest

from smallest_qa.config import settings
from smallest_qa.utils import live
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.utils.retry import with_backoff
from smallest_qa.waves import tts
from smallest_qa.waves.payloads import tts_body, ws_payload

LONG = ("This is a longer answer so that generation is still running when the next request arrives. "
        "It keeps the account's single slot busy for a few seconds.")


def _parallel(n: int, call) -> list:
    barrier, out = threading.Barrier(n), [None] * n

    def worker(i):
        barrier.wait()
        out[i] = call(i)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


def test_second_http_request_gets_429_with_retry_after():
    results = _parallel(2, lambda i: tts.synthesize(tts_body(text=LONG), label=f"parallel-{i}"))
    summary = " | ".join(map(str, results))
    statuses = sorted(r.status for r in results)
    assert statuses == [200, 429], f"documented: one 200, one 429. Got {statuses}: {summary}"
    limited = next(r for r in results if r.status == 429)
    body = limited.json if isinstance(limited.json, dict) else {}
    assert "retry-after" in limited.headers, f"429 without Retry-After: {limited}"
    assert body.get("message") or body.get("error"), f"429 body does not say what happened: {limited}"


def test_documented_backoff_recovers_every_request():
    """Three parallel callers each retry the documented way; all must end in 200 within 6 attempts."""
    runs = _parallel(3, lambda i: with_backoff(
        lambda: tts.synthesize(tts_body(text=f"Caller {i + 1} is checking in."), label=f"backoff-{i}"),
        label=f"backoff-caller-{i}"))
    finals = [r.final.status if r.final else None for r in runs]
    detail = [{"statuses": r.statuses, "total_s": r.total_s} for r in runs]
    assert finals == [200, 200, 200], f"final statuses {finals}: {detail}"


def test_docs_async_sample_saves_only_audio():
    """What a customer copying the docs' asyncio.gather sample ends up with on disk."""
    results = _parallel(3, lambda i: tts.synthesize(tts_body(text=f"Sample request {i + 1}."), label=f"docs-async-{i}"))
    saved = [r.audio_format or f"not audio ({r.status})" for r in results]
    assert saved == ["wav"] * 3, f"files the sample would write as .wav: {saved} | " + " | ".join(map(str, results))


def test_one_slot_is_shared_across_websocket_and_http():
    """While a WebSocket request is generating, an HTTP request must get the documented 429."""
    async def go():
        async with live.live(label="shared-slot-ws") as s:
            sent = await s.send(ws_payload(text=LONG))
            await s.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent)
            rest = await asyncio.to_thread(tts.synthesize, tts_body(text="Meanwhile over HTTP."),
                                           label="shared-slot-http")
            await s.wait_for(lambda f: f.get("status") == "complete", timeout=20, since=sent)
            return rest, s.errors()

    rest, ws_errors = asyncio.run(go())
    assert rest.status == 429, f"HTTP during a WebSocket generation: {rest} (docs: 1 slot across transports)"
    assert not ws_errors, f"the WebSocket request was disturbed: {ws_errors}"


def test_extra_websocket_request_is_rejected_clearly_and_socket_recovers():
    """Docs: the extra request is 'rejected with an error'. The error frame should say why and carry a request
    id, and the rejected socket must be usable once the slot frees up."""
    async def go():
        async with live.live(label="ws-busy-A") as a, live.live(label="ws-busy-B") as b:
            sent_a = await a.send(ws_payload(text=LONG))
            await a.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent_a)
            sent_b = await b.send(ws_payload(text="Second socket, same moment."))
            first_b = await b.wait_for(lambda f: True, timeout=10, since=sent_b)
            await a.wait_for(lambda f: f.get("status") == "complete", timeout=30, since=sent_a)
            retry_b = await b.send(ws_payload(text="Second socket, after the slot is free."))
            served = await b.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=retry_b)
            return first_b, bool(served), b.closed_at, (b.close_code, b.close_reason)

    first_b, served, closed_at, close = asyncio.run(go())
    problems = []
    if not first_b:
        problems.append("no reply at all to the extra request within 10 s")
    elif first_b.get("status") == "chunk":
        problems.append("extra request was served, not rejected (docs: 1 request across sockets)")
    elif not (first_b.get("message") and first_b.get("request_id")):
        problems.append(f"error frame lacks message or request_id: {first_b}")
    if not served:
        problems.append(f"rejected socket not usable afterwards (closed_at={closed_at}, close={close})")
    assert not problems, f"{problems} | first frame: {first_b}"


def test_four_intermittent_conversations():
    """Docs: about 4 parallel conversations per concurrency unit, because callers speak intermittently. Four
    sockets, three short turns each, staggered with think time; at least 75% of turns should be served and every
    rejected turn must get an explicit error (not silence)."""
    if settings.max_in_flight < 4:
        pytest.skip("needs 4 sockets at once: run with QA_MAX_IN_FLIGHT=4 (the brief allows about five)")
    replies = ["Sure, one moment.", "Your table is booked for seven.", "Anything else today?"]

    async def conversation(k: int) -> list[str]:
        outcomes = []
        async with live.live(label=f"conv-{k}") as s:
            await asyncio.sleep(k * 0.7)  # conversations start staggered
            for n, text in enumerate(replies):
                cid = f"qa-conv{k}-{n}-{RUN_ID}"
                sent = await s.send(ws_payload(text=text, context_id=cid, **{"continue": False}))
                f = await s.wait_for(lambda f: f.get("status") in ("chunk", "error") or "error" in f, timeout=10,
                                     since=sent)
                outcomes.append("served" if f and f.get("status") == "chunk" else "rejected" if f else "silent")
                await s.wait_for(lambda f: f.get("status") == "complete", timeout=15, since=sent)
                await asyncio.sleep(2.5)  # caller talks
        return outcomes

    async def go():
        return await asyncio.gather(*(conversation(k) for k in range(4)))

    outcomes = [o for conv in asyncio.run(go()) for o in conv]
    served = outcomes.count("served") / len(outcomes)
    assert "silent" not in outcomes and served >= 0.75, f"served {served:.0%}: {outcomes}"

