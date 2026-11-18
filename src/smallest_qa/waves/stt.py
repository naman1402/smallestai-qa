"""Pulse speech-to-text, pre-recorded: POST /waves/v1/stt/?model=pulse&language=<code>, raw WAV body.

Used by the e2e prototype (caller audio -> text) and to check synthesized audio is intelligible. The service
returns 429 at about one request per second with no Retry-After, so callers should space or retry requests.
"""

import difflib
import re
import unicodedata

from smallest_qa.utils.http import USE_KEY, Exchange, request


def transcribe(wav: bytes, language: str = "en", *, model: str = "pulse", auth=USE_KEY, label: str = "stt") -> Exchange:
    return request("POST", "/waves/v1/stt/", params={"model": model, "language": language},
                   headers={"Content-Type": "audio/wav"}, data=wav, auth=auth, label=label)


def text(ex: Exchange) -> str:
    return (ex.json or {}).get("transcription", "") if isinstance(ex.json, dict) else ""


def _norm(s: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", s).lower())


def similarity(expected: str, heard: str) -> float:
    """Character similarity 0-1 after normalising case, punctuation and spacing."""
    return round(difflib.SequenceMatcher(None, _norm(expected), _norm(heard)).ratio(), 2)
