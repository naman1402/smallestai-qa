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


_MP3_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}  # by MPEG version bits
_MP3_KBPS = {3: (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
             2: (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)}


def mp3_info(data: bytes) -> dict | None:
    """sample_rate, channels, bitrate of the first MPEG layer III frame; duration estimated as CBR."""
    pos = 0
    if data[:3] == b"ID3" and len(data) >= 10:
        pos = 10 + ((data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F))
    while pos + 4 <= len(data):
        b1 = data[pos + 1]
        if data[pos] == 0xFF and b1 & 0xE0 == 0xE0 and (b1 >> 1) & 3 == 1:  # sync + layer III
            ver, b2 = (b1 >> 3) & 3, data[pos + 2]
            if ver in _MP3_RATES and (b2 >> 2) & 3 < 3 and 0 < b2 >> 4 < 15:
                kbps = _MP3_KBPS[3 if ver == 3 else 2][b2 >> 4]
                return {"sample_rate": _MP3_RATES[ver][(b2 >> 2) & 3], "channels": 1 if data[pos + 3] >> 6 == 3 else 2,
                        "bitrate_kbps": kbps, "duration_s": round((len(data) - pos) * 8 / (kbps * 1000), 3)}
        pos += 1
    return None


def duration(data: bytes, sample_rate: int) -> float | None:
    """Seconds of audio, whatever came back: WAV/MP3 from their headers, anything else as 16-bit mono PCM."""
    kind = sniff(data)
    if kind == "wav":
        return (wav_info(data) or {}).get("duration_s")
    if kind == "mp3":
        return (mp3_info(data) or {}).get("duration_s")
    return pcm_duration(len(data), sample_rate) if data else None
