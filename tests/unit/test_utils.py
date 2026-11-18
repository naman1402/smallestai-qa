"""Offline checks of the harness itself: no network, no key needed."""

import json
import struct

import pytest

from smallest_qa.utils import audio, evidence, http
from smallest_qa.waves.payloads import DROP, tts_body


def _wav(rate=24000, channels=1, bits=16, n_samples=24000, data_size=None) -> bytes:
    data = b"\x00\x00" * n_samples * channels
    size = len(data) if data_size is None else data_size
    fmt = struct.pack("<HHIIHH", 1, channels, rate, rate * channels * bits // 8, channels * bits // 8, bits)
    return b"RIFF" + struct.pack("<I", (36 + size) & 0xFFFFFFFF) + b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt + \
        b"data" + struct.pack("<I", size) + data


def test_redact_masks_keys_and_tokens():
    line = evidence.redact(json.dumps({"u": "wss://x/?api_key=wat_abc-DEF_9", "k": "sk_live_SELFTEST123",
                                       "t": "wct_zz"}))
    assert "SELFTEST" not in line and "wat_abc" not in line and "wct_zz" not in line, line


def test_header_dict_drops_cookies_and_joins_repeats():
    h = evidence.header_dict([("Set-Cookie", "a=1"), ("Set-Cookie", "b=2"), ("X-A", "1"), ("X-A", "2")])
    assert h == {"Set-Cookie": "<cookie redacted>", "X-A": "1, 2"}


def test_wav_info_reads_header_and_duration():
    info = audio.wav_info(_wav(rate=24000, n_samples=12000))
    assert info == {"sample_rate": 24000, "channels": 1, "bits": 16, "data_bytes": 24000, "duration_s": 0.5}


def test_wav_info_tolerates_streamed_unknown_size():
    assert audio.wav_info(_wav(n_samples=24000, data_size=0xFFFFFFFF))["duration_s"] == 1.0


@pytest.mark.parametrize("data,expected", [
    (b"ID3\x04....", "mp3"), (b"\xff\xfb\x90\x00", "mp3"),
    (b"\xff\xff\xff\xff", None),  # silent int16 PCM must not look like MP3
    (b'{"error":"x"}', None),
])
def test_sniff(data, expected):
    assert audio.sniff(data) == expected


def test_payload_drop_removes_field():
    assert "voice_id" not in tts_body(voice_id=DROP)


def test_in_flight_guard_refuses_past_limit():
    n = http.settings.max_in_flight
    held = [http._slots.acquire(blocking=False) for _ in range(n)]
    try:
        assert all(held)
        with pytest.raises(RuntimeError, match="in flight"), http.in_flight():
            pass
    finally:
        for _ in held:
            http._slots.release()


def test_mp3_info_reads_frame_header_after_id3():
    # ID3v2 tag (10-byte header, 0 body) then an MPEG-2 layer III frame: 24000 Hz, 64 kbps, mono
    frame = bytes([0xFF, 0xF3, (8 << 4) | (1 << 2), 0xC0]) + b"\x00" * 188
    info = audio.mp3_info(b"ID3\x04\x00\x00\x00\x00\x00\x00" + frame)
    assert info["sample_rate"] == 24000 and info["bitrate_kbps"] == 64 and info["channels"] == 1
    assert audio.duration(b"\x00\x00" * 24000, 24000) == 1.0  # headerless -> 16-bit mono PCM
