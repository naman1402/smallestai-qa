"""AgentSession: one support call over the TTS WebSocket.

A turn streams LLM tokens into a `context_id` in small word groups, closes the context, and measures what
the caller experiences: time to first audio, audio length, and whether playback ever runs dry.
"Agent finished speaking" is detected by audio going quiet, not by `complete`, which arrives ~4 s after
the last chunk (product workaround). Barge-in sends `cancel_request` and gates (drops) the turn's audio
on the client, because the server keeps streaming released audio after a cancel.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from smallest_qa.app.profile import VoiceProfile
from smallest_qa.utils.live import LiveSocket


@dataclass
class TurnMetrics:
    context_id: str
    first_sent_ms: float
    ttfa_ms: float | None = None  # first fragment sent -> first audio chunk
    audio_s: float = 0.0
    min_headroom_s: float | None = None  # playback simulation; negative = audible gap
    max_gap_ms: float = 0.0
    request_ids: list = field(default_factory=list)
    cancelled_at_ms: float | None = None
    talk_over_s: float = 0.0  # audio the server still sent after the cancel (dropped by the client gate)


def playback(events: list[tuple[float, int]], bytes_per_s: int, jitter_ms: float = 150) -> tuple[float, float]:
    """(min headroom s, max gap ms) for a player that starts at the first chunk plus a jitter buffer."""
    if not events:
        return 0.0, 0.0
    t0, have, worst, gap = events[0][0], 0.0, None, 0.0
    for i, (t, n) in enumerate(events):
        played = max(0.0, (t - t0 - jitter_ms) / 1000)
        if i:
            worst = min(worst, have - played) if worst is not None else have - played
            gap = max(gap, t - events[i - 1][0])
        have += n / bytes_per_s
    return round(worst or 0.0, 3), round(gap, 1)


class AgentSession:
    def __init__(self, sock: LiveSocket, profile: VoiceProfile, sample_rate: int = 24000, group_words: int = 3,
                 extra: dict | None = None):
        self.sock, self.profile, self.rate, self.group = sock, profile, sample_rate, group_words
        self.extra = extra or {}

    def _msg(self, cid: str, text: str | None, more: bool) -> dict:
        m = {"context_id": cid, "voice_id": self.profile.voice_id, "model": self.profile.model,
             "sample_rate": self.rate, "continue": more, **self.extra}
        if text is not None:
            m["text"] = text
        if self.profile.dict_ids:
            m["pronunciation_dicts"] = self.profile.dict_ids
        return m

    async def say(self, tokens: AsyncIterator[str], cid: str) -> TurnMetrics:
        """Stream tokens into the context in word groups (flushing at punctuation), then close the context."""
        first, buf = None, []
        async for tok in tokens:
            buf.append(tok)
            if len(buf) >= self.group or tok.rstrip().endswith((".", "?", "!", ",")):
                t = await self.sock.send(self._msg(cid, "".join(buf), True))
                first, buf = first if first is not None else t, []
        if buf:
            t = await self.sock.send(self._msg(cid, "".join(buf), True))
            first = first if first is not None else t
        await self.sock.send(self._msg(cid, None, False))
        return TurnMetrics(cid, first if first is not None else self.sock.now())

    async def finish(self, turn: TurnMetrics, quiet_s: float = 1.0, timeout: float = 30) -> TurnMetrics:
        """Wait until the agent's audio goes quiet; fill in the caller-side metrics."""
        first = await self.sock.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=turn.first_sent_ms)
        if not first:
            return turn
        last = await self.sock.quiet(quiet_s, since=first["t"], timeout=timeout) or self.sock.now()
        chunks = [f for f in self.sock.chunks_after(turn.first_sent_ms) if f["t"] <= last]
        if turn.cancelled_at_ms is not None:
            after = [f for f in chunks if f["t"] > turn.cancelled_at_ms]
            turn.talk_over_s = round(sum(f["data"]["audio_bytes"] for f in after) / (self.rate * 2), 2)
            chunks = [f for f in chunks if f["t"] <= turn.cancelled_at_ms]  # the client gate drops the rest
        events = [(f["t"], f["data"]["audio_bytes"]) for f in chunks]
        turn.ttfa_ms = round(first["t"] - turn.first_sent_ms, 1)
        turn.audio_s = round(sum(n for _, n in events) / (self.rate * 2), 2)
        turn.min_headroom_s, turn.max_gap_ms = playback(events, self.rate * 2)
        turn.request_ids = sorted({f.get("request_id") for f in chunks if f.get("request_id")})
        return turn

    async def interrupt(self, turn: TurnMetrics) -> float:
        """Caller barges in: cancel server-side and gate the turn's audio client-side."""
        turn.cancelled_at_ms = await self.sock.send({"context_id": turn.context_id, "cancel_request": True})
        return turn.cancelled_at_ms

    async def keepalive(self, every_s: float = 2.0):
        """Run as a task for the whole call: real agents ping on a timer, not only between turns."""
        while True:
            await asyncio.sleep(every_s)
            await self.sock.ping()
