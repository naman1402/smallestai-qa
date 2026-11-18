"""A live TTS WebSocket for multi-message scenarios: voice-agent turns, barge-in, keep-alive, reconnects.

`ws.exchange` covers one request per socket. A `LiveSocket` stays open while a background task reads every
frame and stamps it with ms since the socket opened, so a test can send at any moment (fragments, cancel,
ping) and then ask timing questions relative to any send: time to first audio, audio after a cancel, when
the server closed. Base64 audio is decoded and dropped from the frame record; only its byte count is kept.
"""

import asyncio
import base64
import json
import time
from contextlib import asynccontextmanager

from websockets.exceptions import ConnectionClosed

from smallest_qa.utils import evidence, ws
from smallest_qa.utils.http import USE_KEY, ms


class LiveSocket:
    def __init__(self, sock, label: str):
        self.sock, self.label = sock, label
        self.t0 = time.perf_counter()
        self.frames: list[dict] = []  # {"t": ms, **frame}; chunks carry audio_bytes instead of audio
        self.sent: list[dict] = []  # {"t": ms, "msg": payload}
        self.audio: dict[str, bytearray] = {}  # request_id -> PCM
        self.close_code: int | None = None
        self.close_reason: str | None = None
        self.closed_at: float | None = None
        self._reader = asyncio.create_task(self._read())

    def now(self) -> float:
        return ms(time.perf_counter() - self.t0)

    async def send(self, msg: dict) -> float:
        """Send one JSON message; returns its send time (ms since open)."""
        t = self.now()
        await self.sock.send(json.dumps(msg))
        self.sent.append({"t": t, "msg": evidence.shorten(msg)})
        return t

    async def ping(self, kind: str = "ping") -> float:
        return await self.send({"type": kind})

    async def _read(self):
        try:
            async for raw in self.sock:
                t = self.now()
                if isinstance(raw, bytes):
                    self.frames.append({"t": t, "binary_bytes": len(raw)})
                    continue
                frame = json.loads(raw)
                data = frame.get("data") if isinstance(frame.get("data"), dict) else None
                if data and data.get("audio"):
                    pcm = base64.b64decode(data["audio"])
                    self.audio.setdefault(frame.get("request_id") or "", bytearray()).extend(pcm)
                    frame = {**frame, "data": {**data, "audio": None, "audio_bytes": len(pcm)}}
                self.frames.append({"t": t, **frame})
        except ConnectionClosed:
            pass
        finally:
            # a clean close ends the loop without an exception; the connection keeps the code either way
            # (1006 = no close frame, e.g. a dropped network)
            self.close_code, self.close_reason = self.sock.close_code, self.sock.close_reason
            self.closed_at = self.now()

    # --- queries -------------------------------------------------------------------------------------------
    def after(self, t: float, status: str | None = None) -> list[dict]:
        return [f for f in self.frames if f["t"] >= t and (status is None or f.get("status") == status)]

    def chunks_after(self, t: float) -> list[dict]:
        return self.after(t, "chunk")

    def first_chunk_ms(self, sent_at: float) -> float | None:
        """Time from a send to the first audio chunk after it (time to first audio)."""
        c = self.chunks_after(sent_at)
        return round(c[0]["t"] - sent_at, 1) if c else None

    def errors(self) -> list[dict]:
        return [f for f in self.frames if f.get("status") == "error" or "error" in f or "error_code" in f]

    def audio_bytes_after(self, t: float) -> int:
        return sum((f.get("data") or {}).get("audio_bytes", 0) for f in self.chunks_after(t))

    async def wait_for(self, pred, timeout: float, since: float = 0.0) -> dict | None:
        """First frame at/after `since` matching pred, waiting up to `timeout` s (None if none, or closed)."""
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            hit = next((f for f in self.frames if f["t"] >= since and pred(f)), None)
            if hit or self._reader.done():
                return hit
            await asyncio.sleep(0.02)
        return None

    async def quiet(self, seconds: float, since: float = 0.0, timeout: float = 30.0) -> float | None:
        """Wait until no frame has arrived for `seconds`; returns the last frame's time (or None on timeout)."""
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            last = max([f["t"] for f in self.frames if f["t"] >= since] or [since])
            if self.now() - last >= seconds * 1000 or self._reader.done():
                return last
            await asyncio.sleep(0.05)
        return None

    async def wait_closed(self, timeout: float) -> bool:
        try:
            await asyncio.wait_for(asyncio.shield(self._reader), timeout)
        except TimeoutError:
            return False
        return True

    def summary(self) -> dict:
        return {"sent": self.sent[:400], "frames": self.frames[:3000], "n_frames": len(self.frames),
                "audio_bytes": {k: len(v) for k, v in self.audio.items()}, "close_code": self.close_code,
                "close_reason": self.close_reason, "closed_at_ms": self.closed_at}


@asynccontextmanager
async def live(query: str = "", *, auth=USE_KEY, label: str = "live"):
    """Open a LiveSocket (counted against the in-flight cap); logs its full timeline to evidence on exit."""
    async with ws.connect(query=query, auth=auth, label=label) as sock:
        s = LiveSocket(sock, label)
        try:
            yield s
        finally:
            evidence.log(label=label, event="live_socket", **s.summary())
            s._reader.cancel()
