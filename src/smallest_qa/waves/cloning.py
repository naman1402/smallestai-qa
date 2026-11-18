"""Instant voice cloning.

Create  POST   /waves/v1/voice-cloning     multipart: displayName, file, model, language, …
List    GET    /waves/v1/voice-cloning
Delete  DELETE /waves/v1/lightning-large   json {"voiceId": …}  (the docs admit the path is misleading)
"""

import mimetypes
from pathlib import Path

from smallest_qa.utils import evidence
from smallest_qa.utils.http import USE_KEY, Exchange, request


def create(sample: Path | None, *, name: str, mime: str | None = None, auth=USE_KEY, **fields) -> Exchange:
    """Always multipart, even with no file part, so the 'missing file' case is tested the way a form sends it."""
    form = {"displayName": name, **fields}
    files = {k: (None, str(v)) for k, v in form.items()}
    if sample is not None:
        sample = Path(sample)
        mime = mime or mimetypes.guess_type(sample.name)[0] or "application/octet-stream"
        files["file"] = (sample.name, sample.read_bytes(), mime)
    evidence.log(label=f"clone-create:{name}:upload", fields=form, file=sample.name if sample else None,
                 file_bytes=sample.stat().st_size if sample else None, mime=mime)
    return request("POST", "/waves/v1/voice-cloning", auth=auth, label=f"clone-create:{name}", files=files)


def voice_id(ex: Exchange) -> str | None:
    data = ex.json if isinstance(ex.json, dict) else {}
    return (data.get("data") or {}).get("voiceId")


def list_clones(*, auth=USE_KEY) -> Exchange:
    return request("GET", "/waves/v1/voice-cloning", auth=auth, label="clone-list")


def find(ex: Exchange, vid: str) -> dict | None:
    data = ex.json if isinstance(ex.json, dict) else {}
    return next((c for c in data.get("data", []) if c.get("voiceId") == vid), None)


def delete(vid: str, *, auth=USE_KEY) -> Exchange:
    return request("DELETE", "/waves/v1/lightning-large", auth=auth, label=f"clone-delete:{vid}", json={"voiceId": vid})
