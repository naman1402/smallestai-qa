"""Voice catalog: GET /waves/v1/{model}/get_voices."""

from smallest_qa.utils.http import USE_KEY, Exchange, request


def list_voices(model: str = "lightning-v3.1-pro", *, auth=USE_KEY) -> Exchange:
    return request("GET", f"/waves/v1/{model}/get_voices", auth=auth, label=f"voices:{model}")


def voice_ids(ex: Exchange) -> list[str]:
    data = ex.json
    voices = data.get("voices", data) if isinstance(data, dict) else data
    if not isinstance(voices, list):
        return []
    return [v.get("voiceId") or v.get("voice_id") for v in voices if isinstance(v, dict)]
