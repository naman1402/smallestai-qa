"""Default request bodies. Override any field; pass DROP to remove one."""

PRO_VOICE = "meher"  # docs' Lightning v3.1 Pro example voice
V31_VOICE = "magnus"  # docs' Lightning v3.1 (standard catalog) example voice
PRO_MODEL = "lightning_v3.1_pro"
V31_MODEL = "lightning_v3.1"  # retiring 2026-11-30 18:30 UTC
DROP = object()


def _merge(base: dict, over: dict) -> dict:
    return {k: v for k, v in {**base, **over}.items() if v is not DROP}


def tts_body(**over) -> dict:
    """REST/SSE body for POST /waves/v1/tts and /tts/live."""
    return _merge({"text": "Testing one two three.", "voice_id": PRO_VOICE, "model": PRO_MODEL,
                   "sample_rate": 24000, "output_format": "wav"}, over)


def ws_payload(**over) -> dict:
    """One request message on wss://…/waves/v1/tts/live (audio arrives as base64 PCM)."""
    return _merge({"text": "Testing one two three.", "voice_id": PRO_VOICE, "model": PRO_MODEL,
                   "sample_rate": 24000}, over)
