"""The retry policy Smallest documents for 429s, so recovery is tested the way customers are told to retry.

docs/reference/smallest-docs-2026-11-18/models__troubleshooting__error-reference.md, 429 Too Many Requests:
  "Retry with exponential backoff starting at 500 ms, doubling up to 30 s. Respect the Retry-After header
   if present."
"""

import time
from dataclasses import dataclass, field

from smallest_qa.utils import evidence
from smallest_qa.utils.http import Exchange

BASE_S, CAP_S = 0.5, 30.0


@dataclass
class Attempts:
    final: Exchange | None = None
    tries: list[dict] = field(default_factory=list)  # {"status", "request_id", "waited_s", "retry_after"}
    total_s: float = 0.0

    @property
    def statuses(self) -> list:
        return [t["status"] for t in self.tries]


def with_backoff(call, *, max_attempts: int = 6, label: str = "retry") -> Attempts:
    """Run `call()` (returns an Exchange) until it is not a 429, following the documented policy."""
    out, delay, t0 = Attempts(), BASE_S, time.perf_counter()
    for _ in range(max_attempts):
        ex = call()
        retry_after = ex.headers.get("retry-after")
        out.tries.append({"status": ex.status, "request_id": ex.request_id, "retry_after": retry_after})
        out.final = ex
        if ex.status != 429:
            break
        if retry_after and retry_after.replace(".", "", 1).isdigit():
            wait = min(float(retry_after), CAP_S)
        else:
            wait, delay = delay, min(delay * 2, CAP_S)
        out.tries[-1]["waited_s"] = wait
        time.sleep(wait)
    out.total_s = round(time.perf_counter() - t0, 2)
    evidence.log(label=label, event="retry", tries=out.tries, total_s=out.total_s)
    return out
