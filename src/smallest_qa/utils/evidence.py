"""Append-only JSONL evidence log.

One line per HTTP/WebSocket exchange, with UTC and IST timestamps, the test that
made it, and a run ID. Keys and tokens are redacted before anything is written.
Files: evidence/<IST date>.jsonl
"""

import datetime as dt
import json
import re
import threading
import uuid

from smallest_qa.config import settings

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
RUN_ID = uuid.uuid4().hex[:8]  # one per process: groups a pytest session or CLI call
_SECRET = re.compile(r"\b(sk|wat|wct)_[A-Za-z0-9_\-]+")
_ACCOUNT_ID = re.compile(r'("organizationId": ?)"[^"]*"')  # account identifier in API bodies
_lock = threading.Lock()
_current_test = "manual"  # set by the pytest fixture; a plain global so worker threads see it


def set_test(name: str) -> None:
    global _current_test
    _current_test = name


def redact(text: str) -> str:
    if settings.api_key:
        text = text.replace(settings.api_key, "sk_...")
    text = _ACCOUNT_ID.sub(r'\1"<redacted>"', text)
    return _SECRET.sub(lambda m: m.group(1) + "_...", text)


def stamp() -> dict:
    now = dt.datetime.now(dt.UTC)
    return {
        "ts_utc": now.isoformat(timespec="milliseconds"),
        "ts_ist": now.astimezone(IST).isoformat(timespec="milliseconds"),
    }


def log(**record) -> dict:
    """Write one redacted record and return the redacted copy."""
    record = {**stamp(), "run": RUN_ID, "test": _current_test, **record}
    line = redact(json.dumps(record, default=str, ensure_ascii=False))
    path = settings.evidence_dir / f"{record['ts_ist'][:10]}.jsonl"
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(line + "\n")
    return json.loads(line)


def header_dict(items) -> dict:
    """Headers as a dict: repeated names joined, cookie values dropped."""
    out: dict[str, str] = {}
    for k, v in items:
        v = "<cookie redacted>" if k.lower() == "set-cookie" else v
        out[k] = f"{out[k]}, {v}" if k in out and out[k] != v else v
    return out


def shorten(payload):
    """A request body as logged: long text is replaced by its length."""
    if isinstance(payload, dict) and isinstance(payload.get("text"), str) and len(payload["text"]) > 80:
        return {**payload, "text": f"<{len(payload['text'])} chars>"}
    return payload
