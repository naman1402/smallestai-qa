"""Pronunciation dictionaries: /waves/v1/pronunciation-dicts (POST create, GET list, PUT update, DELETE).

Items are {"word", "pronunciation"}; the pronunciation is plain respelling, not IPA.
"""

from smallest_qa.utils.http import USE_KEY, Exchange, request

PATH = "/waves/v1/pronunciation-dicts"


def create(items: list[dict], *, auth=USE_KEY) -> Exchange:
    return request("POST", PATH, auth=auth, label="dict-create", json={"items": items})


def list_dicts(*, auth=USE_KEY) -> Exchange:
    return request("GET", PATH, auth=auth, label="dict-list")


def update(dict_id: str, items: list[dict], *, auth=USE_KEY) -> Exchange:
    return request("PUT", PATH, auth=auth, label="dict-update", json={"id": dict_id, "items": items})


def delete(dict_id: str, *, auth=USE_KEY) -> Exchange:
    return request("DELETE", PATH, auth=auth, label="dict-delete", json={"id": dict_id})


def find(ex: Exchange, dict_id: str) -> dict | None:
    data = ex.json
    items = data if isinstance(data, list) else (data or {}).get("data", []) if isinstance(data, dict) else []
    return next((d for d in items if isinstance(d, dict) and d.get("id") == dict_id), None)
