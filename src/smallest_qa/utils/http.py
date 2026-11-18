"""One logged HTTP exchange, plus the guard that keeps us inside the brief's concurrency rule."""

import json
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

import requests

from smallest_qa.config import settings
from smallest_qa.utils import audio, evidence

USE_KEY = object()  # sentinel: authenticate with SMALLEST_API_KEY
_slots = threading.BoundedSemaphore(settings.max_in_flight)


@contextmanager
def in_flight():
    """Count one request or open socket; refuse (never queue) past the limit."""
    if not _slots.acquire(blocking=False):
        raise RuntimeError(f"more than {settings.max_in_flight} requests in flight; the brief allows about five")
    try:
        yield
    finally:
        _slots.release()


def auth_header(auth) -> dict:
    token = settings.api_key if auth is USE_KEY else auth
    return {"Authorization": f"Bearer {token}"} if token else {}


@dataclass(repr=False)
class Exchange:
    method: str
    path: str
    status: int | None
    headers: dict = field(default_factory=dict)  # lower-case names
    body: bytes = b""
    headers_ms: float | None = None
    ttfb_ms: float | None = None
    total_ms: float | None = None
    error: str | None = None

    @property
    def json(self):
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def request_id(self) -> str | None:
        return self.headers.get("x-request-id")

    @property
    def audio_format(self) -> str | None:
        return audio.sniff(self.body)

    def __str__(self) -> str:  # used in assertion messages, so failures carry their evidence
        if self.audio_format:
            body = f"<{len(self.body)} bytes {self.audio_format}>"
        else:
            body = self.body[:200].decode("utf-8", "replace")
        return (f"{self.method} {self.path} -> {self.status or self.error} "
                f"(x-request-id={self.request_id}, {self.total_ms} ms) {body}")

    __repr__ = __str__


def ms(seconds: float | None) -> float | None:
    return None if seconds is None else round(seconds * 1000, 1)


def excerpt(body: bytes, content_type: str) -> dict:
    fmt = audio.sniff(body)
    if fmt or content_type.startswith("audio/"):
        return {"bytes": len(body), "format": fmt, "wav": audio.wav_info(body)}
    try:
        return {"bytes": len(body), "json": json.loads(body)}
    except ValueError:
        return {"bytes": len(body), "text": body[:400].decode("utf-8", "replace")}


def request(method: str, path: str, *, auth=USE_KEY, headers=None, label: str = "", **kwargs) -> Exchange:
    """Send one request to BASE_URL+path, stream the body, log it, return an Exchange. Never raises on HTTP errors."""
    h = {**auth_header(auth), **(headers or {})}
    req = {"method": method, "path": path, "label": label, "req_json": evidence.shorten(kwargs.get("json")),
           "req_data": kwargs.get("data") if isinstance(kwargs.get("data"), (str, dict)) else None}
    t0 = time.perf_counter()
    with in_flight():
        try:
            r = requests.request(method, settings.base_url + path, headers=h, stream=True, timeout=90, **kwargs)
            t_headers, first, chunks = time.perf_counter() - t0, None, []
            for chunk in r.iter_content(8192):
                first = first if first is not None else time.perf_counter() - t0
                chunks.append(chunk)
            body = b"".join(chunks)
        except requests.RequestException as e:
            evidence.log(**req, error=repr(e), total_ms=ms(time.perf_counter() - t0))
            return Exchange(method, path, None, error=repr(e), total_ms=ms(time.perf_counter() - t0))
    ex = Exchange(method, path, r.status_code, {k.lower(): v for k, v in r.headers.items()}, body,
                  ms(t_headers), ms(first), ms(time.perf_counter() - t0))
    evidence.log(**req, status=ex.status, headers_ms=ex.headers_ms, ttfb_ms=ex.ttfb_ms, total_ms=ex.total_ms,
                 headers=evidence.header_dict(r.headers.items()),
                 body=excerpt(body, r.headers.get("content-type", "")))
    return ex
