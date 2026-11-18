"""Lightning TTS over its three transports.

REST       POST /waves/v1/tts       -> one audio body
SSE        POST /waves/v1/tts/live  -> text/event-stream of base64 audio frames
WebSocket  wss://…/waves/v1/tts/live -> JSON frames: chunk… complete
"""

import base64
import json
import time
from dataclasses import dataclass, field

import requests

from smallest_qa.config import settings
from smallest_qa.utils import evidence, ws
from smallest_qa.utils.http import USE_KEY, Exchange, auth_header, in_flight, ms, request
from smallest_qa.waves.payloads import tts_body


def synthesize(body: dict | None = None, *, auth=USE_KEY, label: str = "tts", **kwargs) -> Exchange:
    """REST synthesis. `body=None` sends the default body; extra kwargs (data=, headers=) pass through for
    malformed-request tests."""
    if "data" not in kwargs:
        kwargs["json"] = tts_body() if body is None else body
    return request("POST", "/waves/v1/tts", auth=auth, label=label, **kwargs)


@dataclass
class SSEResult:
    status: int | None
    headers: dict
    headers_ms: float | None
    first_audio_ms: float | None = None
    total_ms: float | None = None
    events: dict = field(default_factory=dict)  # event name -> count
    frames: list = field(default_factory=list)  # every non-audio data frame + first audio frame envelope
    audio: bytes = b""
    raw_lines: list = field(default_factory=list)  # lines that are neither event: nor data:
    error_body: str | None = None
    audio_events: list = field(default_factory=list)  # (ms since request, audio bytes) per audio event
    stopped_early: bool = False

    @property
    def request_id(self):
        return self.headers.get("x-request-id")

    @property
    def done_frame(self):
        return next((f for f in self.frames if f.get("done") is True), None)


def synthesize_sse(body: dict | None = None, *, auth=USE_KEY, label: str = "tts-sse",
                   stop_after: int | None = None) -> SSEResult:
    """POST /tts/live as SSE. `stop_after=N` closes the stream after N audio events (a client that goes away)."""
    payload = tts_body(output_format="pcm") if body is None else body
    t0 = time.perf_counter()
    with in_flight():
        r = requests.post(settings.base_url + "/waves/v1/tts/live", json=payload, stream=True, timeout=90,
                          headers={**auth_header(auth), "Accept": "text/event-stream"})
        res = SSEResult(r.status_code, {k.lower(): v for k, v in r.headers.items()}, ms(time.perf_counter() - t0))
        if r.status_code != 200:
            res.error_body = r.text[:400]
        else:
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("event:"):
                    name = line[6:].strip()
                    res.events[name] = res.events.get(name, 0) + 1
                elif line.startswith("data:"):
                    frame, t = json.loads(line[5:]), ms(time.perf_counter() - t0)
                    if frame.get("audio"):
                        if res.first_audio_ms is None:
                            res.first_audio_ms = t
                            res.frames.append({"t_ms": t, **frame, "audio": "<base64>"})
                        pcm = base64.b64decode(frame["audio"])
                        res.audio += pcm
                        res.audio_events.append((t, len(pcm)))
                        if stop_after and len(res.audio_events) >= stop_after:
                            res.stopped_early = True
                            r.close()
                            break
                    else:
                        res.frames.append({"t_ms": t, **frame})
                else:
                    res.raw_lines.append(line[:200])
    res.total_ms = ms(time.perf_counter() - t0)
    evidence.log(label=label, method="POST", path="/waves/v1/tts/live", req_json=evidence.shorten(payload),
                 status=res.status, headers=evidence.header_dict(r.headers.items()), headers_ms=res.headers_ms,
                 first_audio_ms=res.first_audio_ms, total_ms=res.total_ms, events=res.events,
                 frames=res.frames[:20], audio_bytes=len(res.audio), raw_lines=res.raw_lines[:10],
                 error_body=res.error_body, audio_events=res.audio_events[:200], stopped_early=res.stopped_early)
    return res


async def synthesize_ws(payload: dict, *, query: str = "", auth=USE_KEY, label: str = "tts-ws",
                        idle: float = 10.0) -> ws.Timeline:
    """Open a socket, send one request, record its frame timeline, close."""
    async with ws.connect(query=query, auth=auth, label=label) as sock:
        return await ws.exchange(sock, payload, label=label, idle=idle)
