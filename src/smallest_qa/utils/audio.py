"""Inspect returned audio without judging how it sounds: format, header fields, duration."""

import struct


def sniff(data: bytes) -> str | None:
    """Container format from magic bytes: 'wav', 'mp3' or None (raw PCM, μ-law, A-law, or not audio)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    # MPEG layer III frame sync; FF FF (an int16 -1 sample in silent PCM) must not match
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and data[1] in (0xFB, 0xFA, 0xF3, 0xF2, 0xE3, 0xE2)):
        return "mp3"
    return None


def wav_info(data: bytes) -> dict | None:
    """sample_rate, channels, bits and duration of a WAV, tolerant of streamed (unknown-size) headers."""
    if sniff(data) != "wav":
        return None
    pos, fmt = 12, None
    while pos + 8 <= len(data):
        cid, size = data[pos : pos + 4], struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        if cid == b"fmt ":
            _, channels, rate, _, _, bits = struct.unpack("<HHIIHH", data[pos + 8 : pos + 24])
            fmt = {"sample_rate": rate, "channels": channels, "bits": bits}
        elif cid == b"data" and fmt:
            payload = len(data) - (pos + 8)  # streamed headers may carry a bogus size; trust the bytes we have
            frame = fmt["channels"] * fmt["bits"] // 8 or 1
            return {**fmt, "data_bytes": payload, "duration_s": round(payload / frame / fmt["sample_rate"], 3)}
        pos += 8 + size + (size & 1)
    return fmt


def pcm_duration(n_bytes: int, sample_rate: int, bits: int = 16, channels: int = 1) -> float:
    return round(n_bytes / (bits // 8 * channels) / sample_rate, 3)
