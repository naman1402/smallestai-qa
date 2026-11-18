"""Connection durability: idle timeouts, keep-alive, close handling, reconnects, socket reuse, bad input,
and a client that drops mid-stream.

Contract: docs/reference/smallest-docs-2026-11-18/api-reference__models__text-to-speech__tts.md
  idle timeout 60 s, closes with {"status": "error", "message": "Connection timed out after 60 seconds of
  inactivity"}; ?timeout=N honored below the cap, clamped to 180 s; {"type": "ping"} -> {"type": "pong"} resets
  the timer, with `keepalive`, `keep_alive`, `keep-alive` accepted as aliases.
models__text-to-speech__streaming.md contradicts itself on reuse: the WebSocket-vs-SSE table says "Multiple
  messages: Reuse same connection", the Response Format says `complete` is terminal and "the server closes the
  WebSocket after this".
The status enum (chunk | word_timestamp | complete) documents no error frame and no close codes.
"""

import asyncio

import pytest

from smallest_qa.utils import live, ws
from smallest_qa.waves.payloads import ws_payload

LONG = ("This is a longer answer so that generation is still running when the connection drops. "
        "It keeps the account's single slot busy for a few seconds.")


def served(s: live.LiveSocket, since: float, timeout: float = 10):
    return s.wait_for(lambda f: f.get("status") in ("chunk", "error") or "error" in f, timeout=timeout, since=since)


def test_idle_timeout_closes_cleanly_and_reconnect_is_served():
    async def go():
        async with live.live(query="timeout=5", label="idle-5s") as s:
            closed = await s.wait_closed(timeout=10)
            idle = {"closed": closed, "closed_at": s.closed_at, "code": s.close_code, "reason": s.close_reason,
                    "frames": s.frames[-3:]}
        async with live.live(label="reconnect") as r:
            sent = await r.send(ws_payload(text="Back again after the timeout."))
            first = await served(r, sent)
            return idle, first, r.first_chunk_ms(sent)

    idle, first, ttfa = asyncio.run(go())
    problems = []
    if not idle["closed"] or not 4000 <= (idle["closed_at"] or 0) <= 7000:
        problems.append(f"closed={idle['closed']} at {idle['closed_at']} ms (asked for 5 s)")
    if not any("timed out" in str(f.get("message", "")).lower() for f in idle["frames"]):
        problems.append("no documented 'Connection timed out' message before the close")
    if idle["code"] in (None, 1006):
        problems.append(f"no close frame (code {idle['code']}): clients cannot tell a timeout from a network drop")
    if not first or first.get("status") != "chunk":
        problems.append(f"reconnect not served: {first}")
    assert not problems, f"{problems} | idle={idle} | reconnect ttfa={ttfa} ms"


@pytest.mark.parametrize("kind", ["ping", "keepalive", "keep_alive", "keep-alive"])
def test_keepalive_message_gets_pong_and_resets_timer(kind):
    async def go():
        async with live.live(query="timeout=5", label=f"keepalive-{kind}") as s:
            await asyncio.sleep(3)
            t = await s.ping(kind)
            pong = await s.wait_for(lambda f: f.get("type") == "pong", timeout=2, since=t)
            await asyncio.sleep(4)  # 7 s after open: past the original 5 s deadline
            return pong, s.closed_at, s.frames[-3:]

    pong, closed_at, frames = asyncio.run(go())
    assert pong and closed_at is None, f"{kind}: pong={pong} closed_at={closed_at} frames={frames}"


@pytest.mark.slow
@pytest.mark.parametrize("query,expected_s", [("", 60), ("timeout=500", 180)], ids=["default_60s", "clamped_180s"])
def test_long_idle_timeouts(query, expected_s):
    async def go():
        async with live.live(query=query, label=f"idle-{expected_s}s") as s:
            await s.wait_closed(timeout=expected_s + 20)
            return s.closed_at

    closed_at = asyncio.run(go())
    assert closed_at and abs(closed_at / 1000 - expected_s) <= 3, f"closed at {closed_at} ms, documented {expected_s} s"


def test_socket_after_complete_is_closed_or_reusable_never_silent():
    """The docs say both 'reuse the same connection' and 'the server closes the WebSocket after complete'.
    Either is workable; a socket that stays open but ignores the next request is not."""
    async def go():
        async with live.live(label="reuse-after-complete") as s:
            a = await s.send(ws_payload(text="First request."))
            await s.wait_for(lambda f: f.get("status") == "complete", timeout=15, since=a)
            await asyncio.sleep(1.0)
            if s.closed_at is not None:
                return {"behavior": "closed", "code": s.close_code, "reason": s.close_reason}
            b = await s.send(ws_payload(text="Second request on the same socket."))
            first = await served(s, b)
            return {"behavior": "open", "second": first, "ttfa_ms": s.first_chunk_ms(b)}

    r = asyncio.run(go())
    if r["behavior"] == "closed":
        assert r["code"] not in (None, 1006), f"closed without a close frame: {r}"
    else:
        assert r["second"] and r["second"].get("status") == "chunk", f"socket open but second request: {r}"


def test_bad_message_gets_an_error_frame_and_socket_survives():
    """Malformed JSON and a request without voice_id should each get an explicit error, and a valid request on
    the same socket afterwards should still be served (one bad message should not cost the conversation)."""
    async def go():
        async with live.live(label="bad-input") as s:
            t1 = s.now()
            await s.sock.send("{not json")
            e1 = await s.wait_for(lambda f: True, timeout=5, since=t1)
            t2 = await s.send({"text": "No voice here."})
            e2 = await s.wait_for(lambda f: True, timeout=5, since=t2)
            t3 = await s.send({"type": "subscribe", "channel": "qa"})  # unknown message type
            e3 = await s.wait_for(lambda f: True, timeout=5, since=t3)
            if s.closed_at is not None:
                return e1, e2, e3, None, (s.close_code, s.close_reason)
            ok = await s.send(ws_payload(text="A valid request after the bad ones."))
            return e1, e2, e3, await served(s, ok), (s.close_code, s.close_reason)

    bad_json, no_voice, unknown, after, close = asyncio.run(go())
    problems = []
    for name, frame in (("malformed JSON", bad_json), ("missing voice_id", no_voice), ("unknown type", unknown)):
        if not frame or not (frame.get("message") or frame.get("error")):
            problems.append(f"{name}: no explicit error frame ({frame})")
    if not after or after.get("status") != "chunk":
        problems.append(f"valid request afterwards not served: {after} close={close}")
    assert not problems, problems


def test_dropped_client_frees_the_slot_quickly():
    """A caller's network drops mid-stream. The account's single slot should free up within ~2 s, otherwise the
    reconnecting agent is rejected while the server finishes audio nobody will hear."""
    async def go():
        async with live.live(label="drop-A") as a:
            sent = await a.send(ws_payload(text=LONG))
            await a.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=sent)
            a.sock.transport.abort()  # no close handshake, like a lost network
        attempts = []
        async with live.live(label="drop-B") as b:
            for _ in range(8):
                t = await b.send(ws_payload(text="Reconnected caller."))
                first = await served(b, t, timeout=5)
                attempts.append({"t": t, "status": first and first.get("status")})
                if first and first.get("status") == "chunk":
                    break
                await asyncio.sleep(1)
                if b.closed_at is not None:
                    break
            return attempts

    attempts = asyncio.run(go())
    ok = [x for x in attempts if x["status"] == "chunk"]
    assert ok and ok[0]["t"] <= 2500, f"slot after a dropped client: {attempts}"


@pytest.mark.parametrize("auth", [None, "sk_qa_invalid_key"], ids=["no_key", "invalid_key"])
def test_handshake_without_valid_key_is_rejected_clearly(auth):
    """websocket-realtime-testing skill: a bad credential should fail the upgrade (HTTP 401) or close with an auth
    code (1008/4401) and a reason, never accept the socket and drop or ignore the request later."""
    async def go():
        try:
            async with live.live(auth=auth, label=f"handshake-{auth and 'invalid' or 'none'}") as s:
                sent = await s.send(ws_payload(text="Should not be spoken."))
                first = await s.wait_for(lambda f: True, timeout=5, since=sent)
                await s.wait_closed(timeout=5)
                return {"accepted": True, "first": first, "code": s.close_code, "reason": s.close_reason}
        except ws.WSRejected as e:
            return {"accepted": False, "status": e.status, "body": e.body[:200]}

    r = asyncio.run(go())
    if not r["accepted"]:
        assert r["status"] in (401, 403), f"handshake rejected with an unexpected status: {r}"
    else:
        first = r["first"] or {}
        assert first.get("status") != "chunk", f"unauthenticated socket was served audio: {r}"
        assert r["code"] in (1008, 4001, 4401, 4403) or first.get("message"), f"accepted then dropped unclearly: {r}"
