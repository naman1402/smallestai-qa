"""Pulse speech-to-text, pre-recorded: POST /waves/v1/stt/?model=pulse&language=<code>, raw WAV body.

Used by the e2e prototype (caller audio -> text) and to check synthesized audio is intelligible. The service
returns 429 at about one request per second with no Retry-After, so callers should space or retry requests.
"""

import difflib
import unicodedata

from smallest_qa.utils.http import USE_KEY, Exchange, request

# Devanagari spelling variants that do not change the word: chandrabindu -> anusvara, nukta dropped
_FOLD = str.maketrans({"ँ": "ं", "़": None})


def transcribe(wav: bytes, language: str = "en", *, model: str = "pulse", auth=USE_KEY, label: str = "stt") -> Exchange:
    return request("POST", "/waves/v1/stt/", params={"model": model, "language": language},
                   headers={"Content-Type": "audio/wav"}, data=wav, auth=auth, label=label)


def text(ex: Exchange) -> str:
    return (ex.json or {}).get("transcription", "") if isinstance(ex.json, dict) else ""


def _words(s: str) -> list[str]:
    """Lower-case NFKC words: letters, combining marks (Devanagari vowel signs) and digits (any script -> ASCII)."""
    s = unicodedata.normalize("NFKC", unicodedata.normalize("NFKD", s).translate(_FOLD)).lower()
    out = []
    for c in s:
        cat = unicodedata.category(c)
        out.append(str(unicodedata.decimal(c)) if cat == "Nd" else c if cat[0] in "LMN" else " ")
    return "".join(out).split()


def normalize(s: str, aliases: dict[str, str] | None = None) -> str:
    """Text without case, punctuation (incl. the danda), symbols or spacing. `aliases` maps whole words to one
    spelling, e.g. a loanword Pulse may write in Latin script ("support") where the text has Devanagari."""
    words = _words(s)
    if aliases:
        table = {"".join(_words(k)): "".join(_words(v)) for k, v in aliases.items()}
        words = [table.get(w, w) for w in words]
    return "".join(words)


_norm = normalize  # earlier name


def similarity(expected: str, heard: str, aliases: dict[str, str] | None = None) -> float:
    """Character similarity 0-1 after normalising case, punctuation and spacing (and `aliases`, if given)."""
    return round(difflib.SequenceMatcher(None, normalize(expected, aliases), normalize(heard, aliases)).ratio(), 2)
