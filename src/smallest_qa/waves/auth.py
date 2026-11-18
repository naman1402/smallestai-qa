"""Short-lived access tokens: POST /console/v1/auth/token (TTL 30-900 s, prefix wat_)."""

from smallest_qa.utils.http import USE_KEY, Exchange, request

MINT_PATH = "/console/v1/auth/token"


def mint(body: dict | None = None, *, auth=USE_KEY, label: str = "token-mint") -> Exchange:
    """The returned Exchange holds the real token in .json; the evidence log only has a redacted copy."""
    return request("POST", MINT_PATH, auth=auth, label=label, json=body)


def token(ex: Exchange) -> str | None:
    return ex.json.get("access_token") if ex.status == 201 and isinstance(ex.json, dict) else None
