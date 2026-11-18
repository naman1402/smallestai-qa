"""VoiceProfile: the brand voice as the product stores it, with onboarding and offboarding steps.

Product decisions taken from earlier findings (each one is a workaround the scorecard reports):
  - trim leading silence from the sample before cloning (a Pro clone can otherwise add a stray opening sound)
  - upload as the browser labels the file; if rejected as "Invalid file type", retry as audio/wav
"""

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from smallest_qa.utils.http import Exchange
from smallest_qa.waves import cloning, pronunciation
from smallest_qa.waves.payloads import PRO_MODEL


@dataclass
class VoiceProfile:
    voice_id: str
    model: str = PRO_MODEL
    dict_ids: list[str] = field(default_factory=list)


def prepare_sample(src: Path, out: Path, seconds: int = 12) -> Path:
    """Mono 24 kHz WAV, leading silence trimmed, cut to `seconds` (the API accepts 5-15 s)."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af",
                    "silenceremove=start_periods=1:start_threshold=-35dB:start_silence=0.05",
                    "-ac", "1", "-ar", "24000", "-t", str(seconds), str(out)], check=True)
    return out


def upload_clone(sample: Path, name: str, browser_mime: str = "audio/x-wav") -> tuple[str | None, list[Exchange]]:
    """Upload the way a web app would (the browser's MIME label), falling back to audio/wav."""
    attempts = [cloning.create(sample, name=name, mime=browser_mime, language="en", model="lightning-v3.1-pro")]
    if attempts[0].status == 400 and b"file type" in attempts[0].body.lower():
        attempts.append(cloning.create(sample, name=name, mime="audio/wav", language="en", model="lightning-v3.1-pro"))
    return cloning.voice_id(attempts[-1]), attempts


def wait_ready(voice_id: str, timeout_s: float = 60) -> tuple[str | None, float]:
    """Poll the clone list until the clone is `completed`; returns (last status, seconds waited)."""
    t0, status = time.perf_counter(), None
    while time.perf_counter() - t0 < timeout_s:
        entry = cloning.find(cloning.list_clones(), voice_id)
        status = (entry or {}).get("status")
        if status in ("completed", "failed"):
            break
        time.sleep(2)
    return status, round(time.perf_counter() - t0, 1)


def dictionary_ids_valid(ids: list[str]) -> list[str]:
    """Product guard: the API accepts deleted dictionary ids silently, so check them against the list first."""
    listing = pronunciation.list_dicts()
    data = listing.json if isinstance(listing.json, list) else (listing.json or {}).get("data", [])
    known = {d.get("id") for d in data if isinstance(d, dict)}
    return [i for i in ids if i in known]
