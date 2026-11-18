"""Lightning TTS output over REST: POST /waves/v1/tts.

Contract: docs/reference/smallest-docs-2026-11-18/api-reference__models__text-to-speech__synthesize-speech.md
  output_format  enum pcm | mp3 | wav, default pcm
  sample_rate    enum 8000 | 16000 | 24000 | 44100, default 44100
A failure is a finding candidate; its message carries the x-request-id to look up in evidence/<date>.jsonl.
"""

from smallest_qa.utils import audio
from smallest_qa.waves import tts
from smallest_qa.waves.payloads import DROP, PRO_VOICE, tts_body

TEXT = "The quick brown fox jumps over the lazy dog near the quiet river bank."  # ~4 s of speech
PLAUSIBLE_S = (2.0, 9.0)  # a header that lies about the rate lands 2-5x outside this
CONTENT_TYPES = {
    "wav": {"audio/wav", "audio/x-wav", "audio/wave"},
    "mp3": {"audio/mpeg", "audio/mp3"},
    "pcm": {"audio/pcm", "audio/l16", "audio/raw", "application/octet-stream"},
}
# every format once, every rate once: browser (mp3), telephony (8 kHz), wideband (16 kHz), hi-fi (44.1 kHz)
COMBOS = [("pcm", 24000), ("mp3", 24000), ("wav", 8000), ("wav", 16000), ("wav", 24000), ("mp3", 44100)]


def test_output_is_what_was_asked_for():
    """Container, header sample rate, Content-Type and duration agree with the request. A customer pipes this
    into a player, a phone bridge or a browser: a wrong rate plays at the wrong pitch, a wrong type won't play."""
    problems = {}
    for fmt, rate in COMBOS:
        ex = tts.synthesize(tts_body(text=TEXT, output_format=fmt, sample_rate=rate), label=f"tts-{fmt}-{rate}")
        if ex.status != 200:
            problems[f"{fmt}@{rate}"] = str(ex)
            continue
        issues = []
        container = ex.audio_format
        if container != (None if fmt == "pcm" else fmt):
            issues.append(f"container {container}")
        header = audio.wav_info(ex.body) if container == "wav" else audio.mp3_info(ex.body) if container else None
        if header and (header.get("sample_rate"), header.get("channels")) != (rate, 1):
            issues.append(f"header {header.get('sample_rate')} Hz / {header.get('channels')} ch")
        seconds = audio.duration(ex.body, rate)
        if not seconds or not PLAUSIBLE_S[0] <= seconds <= PLAUSIBLE_S[1]:
            issues.append(f"{seconds} s for a ~4 s sentence")
        ctype = ex.headers.get("content-type", "").split(";")[0].strip().lower()
        if ctype not in CONTENT_TYPES[fmt]:
            issues.append(f"Content-Type {ctype!r}")
        if issues:
            problems[f"{fmt}@{rate}"] = f"{issues} x-request-id={ex.request_id}"
    assert not problems, problems


def test_minimal_request_uses_documented_defaults():
    """Reference defaults are pcm at 44100 Hz, but every doc example sends wav/24000. A customer who trims the
    body to text + voice_id gets headerless audio; this checks it is at least the documented kind.
    Compared with an explicit pcm/44100 request: a 24 kHz default would be ~0.54x the bytes."""
    minimal = tts.synthesize({"text": TEXT, "voice_id": PRO_VOICE}, label="tts-defaults")
    explicit = tts.synthesize(tts_body(text=TEXT, model=DROP, output_format="pcm", sample_rate=44100),
                              label="tts-explicit-pcm-44100")
    assert minimal.status == 200 and explicit.status == 200, f"{minimal} | {explicit}"
    assert minimal.audio_format is None, f"documented default is pcm, got {minimal.audio_format}: {minimal}"
    ratio = len(minimal.body) / max(len(explicit.body), 1)
    assert 0.8 <= ratio <= 1.25, f"default body is {ratio:.2f}x the explicit 44100 Hz pcm body | {minimal}"
