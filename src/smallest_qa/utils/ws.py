"""WebSocket helpers: open a logged connection and record a request's frame timeline."""

import asyncio
import base64
import json
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field

from websockets.asyncio.client import connect as _connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

from smallest_qa.config import settings
from smallest_qa.utils import evidence
from smallest_qa.utils.http import USE_KEY, auth_header, in_flight, ms


class WSRejected(Exception):
    """The server refused the handshake. Carries what it sent back."""

    def __init__(self, status: int, headers: dict, body: str):
        super().__init__(f"handshake rejected: HTTP {status} body={body[:200]!r}")
        self.status, self.headers, self.body = status, headers, body


@asynccontextmanager
async def connect(path: str = "/waves/v1/tts/live", *, query: str = "", auth=USE_KEY, label: str = ""):
    """Open a socket (counted against the in-flight limit) and close it on exit."""
    url = settings.ws_url + path + ("?" + query if query else "")
    t0 = time.perf_counter()
    with in_flight():
        try:
            # ping_interval=None: protocol pings from the library could reset the server's idle timer
            ws = await _connect(url, additional_headers=auth_header(auth), max_size=None, open_timeout=15,
                                ping_interval=None)
        except InvalidStatus as e:
            r = e.response
            body = (r.body or b"").decode("utf-8", "replace")
            headers = evidence.header_dict(r.headers.raw_items())
            evidence.log(label=label, event="ws_rejected", url=url, status=r.status_code, headers=headers,
                         body=body[:400])
            raise WSRejected(r.status_code, {k.lower(): v for k, v in headers.items()}, body) from None
        evidence.log(label=label, event="ws_open", url=url, connect_ms=ms(time.perf_counter() - t0),
                     headers=evidence.header_dict(ws.response.headers.raw_items()))
        try:
            yield ws
        finally:
            await ws.close()


@dataclass
class Timeline:
    """What happened after one send, in ms from the send."""

    first_chunk_ms: float | None = None
    last_chunk_ms: float | None = None
    complete_ms: list = field(default_factory=list)
    close_ms: float | None = None
    close_code: int | None = None
    close_reason: str | None = None
    chunks: int = 0
    audio: bytes = b""
    frames: list = field(default_factory=list)  # every non-chunk frame, plus the first chunk's envelope
    request_ids: list = field(default_factory=list)
    idle_timeout: bool = False

    @property
    def error_frames(self) -> list:
        return [f for f in self.frames if f.get("status") == "error" or "error" in f or "error_code" in f]

    @property
    def complete_after_last_chunk_ms(self) -> float | None:
        if self.complete_ms and self.last_chunk_ms is not None:
            return round(self.complete_ms[0] - self.last_chunk_ms, 1)
        return None


async def exchange(ws, payload: dict | None = None, *, label: str = "", idle: float = 10.0,
                   until_complete: bool = True, state: dict | None = None) -> Timeline:
    """Send payload (if any), then read frames until complete+close, a close, or `idle` seconds of silence."""
    t0, tl = time.perf_counter(), Timeline()
    if payload is not None:
        await ws.send(json.dumps(payload))
    while True:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=idle)
        except TimeoutError:
            tl.idle_timeout = True
            break
        except ConnectionClosed as e:
            tl.close_ms = ms(time.perf_counter() - t0)
            if e.rcvd:
                tl.close_code, tl.close_reason = e.rcvd.code, e.rcvd.reason
            break
        t = ms(time.perf_counter() - t0)
        if isinstance(msg, bytes):
            tl.frames.append({"t_ms": t, "binary_bytes": len(msg)})
            continue
        frame = json.loads(msg)
        if frame.get("request_id") and frame["request_id"] not in tl.request_ids:
            tl.request_ids.append(frame["request_id"])
        if frame.get("status") == "chunk":
            if tl.chunks == 0:
                tl.frames.append({"t_ms": t, **frame, "data": {"audio": "<base64>"}})
            tl.chunks += 1
            tl.audio += base64.b64decode((frame.get("data") or {}).get("audio", ""))
            tl.first_chunk_ms = tl.first_chunk_ms or t
            tl.last_chunk_ms = t
            if state is not None:
                state["last_chunk_at"] = time.perf_counter()
            continue
        tl.frames.append({"t_ms": t, **frame})
        if frame.get("status") == "complete":
            tl.complete_ms.append(t)
            if until_complete:
                idle = min(idle, 8.0)  # keep reading briefly to time the server's close
    record = {k: v for k, v in asdict(tl).items() if k != "audio"}
    evidence.log(label=label, event="ws_exchange", req_json=evidence.shorten(payload), audio_bytes=len(tl.audio),
                 complete_after_last_chunk_ms=tl.complete_after_last_chunk_ms, **record)
    return tl
