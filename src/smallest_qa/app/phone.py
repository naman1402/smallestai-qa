"""Phone leg without a phone number: G.711 mu-law at 8 kHz in 20 ms frames, paced like a carrier.

Telephony platforms take 8 kHz mu-law in 20 ms frames (160 bytes) and play one frame every 20 ms. A frame
that is not ready on time is an audible gap on the call.
"""

import struct

FRAME_MS, RATE = 20, 8000
FRAME_BYTES = RATE * FRAME_MS // 1000  # 160 mu-law bytes = 20 ms


def _ulaw(sample: int) -> int:
    bias, clip = 0x84, 32635
    sign = 0x80 if sample < 0 else 0
    sample = min(abs(sample), clip) + bias
    exponent, mask = 7, 0x4000
    while exponent > 0 and not sample & mask:
        exponent, mask = exponent - 1, mask >> 1
    mantissa = (sample >> (exponent + 3)) & 0x0F
    return ~(sign | (exponent << 4) | mantissa) & 0xFF


def mulaw_encode(pcm16: bytes) -> bytes:
    """16-bit little-endian PCM -> G.711 mu-law (one byte per sample)."""
    n = len(pcm16) // 2
    return bytes(_ulaw(s) for s in struct.unpack(f"<{n}h", pcm16[: n * 2]))


def frames(ulaw: bytes) -> list[bytes]:
    """Split into 20 ms frames; the last one is padded with mu-law silence (0xFF)."""
    out = [ulaw[i : i + FRAME_BYTES] for i in range(0, len(ulaw), FRAME_BYTES)]
    if out and len(out[-1]) < FRAME_BYTES:
        out[-1] = out[-1] + b"\xff" * (FRAME_BYTES - len(out[-1]))
    return out


def carrier_pacing(arrivals: list[tuple[float, int]], jitter_ms: float = 60.0) -> dict:
    """arrivals: (ms, mu-law bytes) as audio reaches us. The carrier starts playing jitter_ms after the first
    arrival and needs one 160-byte frame every 20 ms. Counts frames that were not ready in time."""
    if not arrivals:
        return {"frames": 0, "late_frames": 0, "worst_late_ms": 0.0}
    start = arrivals[0][0] + jitter_ms
    total = sum(n for _, n in arrivals)
    n_frames = -(-total // FRAME_BYTES)
    late, worst, cum, i = 0, 0.0, 0, 0
    for k in range(n_frames):
        need = min((k + 1) * FRAME_BYTES, total)
        while cum < need:
            t, n = arrivals[i]
            cum, i = cum + n, i + 1
        ready_at = arrivals[i - 1][0]
        due = start + k * FRAME_MS
        if ready_at > due:
            late, worst = late + 1, max(worst, ready_at - due)
    return {"frames": n_frames, "late_frames": late, "worst_late_ms": round(worst, 1),
            "audio_s": round(total / RATE, 2)}
