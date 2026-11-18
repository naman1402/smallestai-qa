"""Go/no-go scorecard for the support-agent prototype.

Each journey records weighted checks against a product threshold. Scoring:
  passed                       -> full weight
  failed, but a workaround     -> half weight (we could ship, at a cost the scorecard names)
  failed, no workaround        -> 0
Verdict:
  NO-GO                 a blocker check failed and has no workaround, or the score is under 70%
  GO WITH WORKAROUNDS   score >= 70% and every failed blocker has a workaround
  GO                    every check passed
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Check:
    journey: str
    name: str
    value: object
    threshold: str
    passed: bool
    weight: int = 1
    blocker: bool = False
    workaround: str | None = None
    evidence: list = field(default_factory=list)  # x-request-ids / session ids
    note: str = ""

    @property
    def points(self) -> float:
        return self.weight if self.passed else self.weight * 0.5 if self.workaround else 0.0

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "WORKAROUND" if self.workaround else "FAIL"


class Scorecard:
    def __init__(self):
        self.checks: list[Check] = []

    def check(self, journey: str, name: str, value, passed: bool, threshold: str, *, weight: int = 1,
              blocker: bool = False, workaround: str | None = None, evidence=(), note: str = "") -> Check:
        c = Check(journey, name, value, threshold, bool(passed), weight, blocker, workaround,
                  [e for e in evidence if e], note)
        self.checks.append(c)
        return c

    def failed(self, journey: str | None = None) -> list[Check]:
        return [c for c in self.checks if not c.passed and (journey is None or c.journey == journey)]

    def score(self, journey: str | None = None) -> float:
        cs = [c for c in self.checks if journey is None or c.journey == journey]
        total = sum(c.weight for c in cs)
        return round(100 * sum(c.points for c in cs) / total, 1) if total else 0.0

    def verdict(self) -> str:
        if any(c.blocker and not c.passed and not c.workaround for c in self.checks):
            return "NO-GO"
        if not self.failed():
            return "GO"
        return "GO WITH WORKAROUNDS" if self.score() >= 70 else "NO-GO"

    def journeys(self) -> list[str]:
        return list(dict.fromkeys(c.journey for c in self.checks))

    def markdown(self) -> str:
        lines = [f"# Support-agent prototype scorecard: **{self.verdict()}** ({self.score()}%)", "",
                 "| Journey | Score | Pass | Workaround | Fail |", "|---|---|---|---|---|"]
        for j in self.journeys():
            cs = [c for c in self.checks if c.journey == j]
            lines.append(f"| {j} | {self.score(j)}% | {sum(c.status == 'PASS' for c in cs)} | "
                         f"{sum(c.status == 'WORKAROUND' for c in cs)} | {sum(c.status == 'FAIL' for c in cs)} |")
        lines += ["", "| Journey | Check | Value | Threshold | Status | Blocker | Workaround / note | Evidence |",
                  "|---|---|---|---|---|---|---|---|"]
        for c in self.checks:
            extra = "; ".join(x for x in (c.workaround, c.note) if x)
            lines.append(f"| {c.journey} | {c.name} | {c.value} | {c.threshold} | {c.status} | "
                         f"{'yes' if c.blocker else ''} | {extra} | {', '.join(f'`{e}`' for e in c.evidence[:3])} |")
        return "\n".join(lines) + "\n"

    def write(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "scorecard.json").write_text(json.dumps(
            {"verdict": self.verdict(), "score": self.score(), "checks": [asdict(c) | {"status": c.status}
                                                                          for c in self.checks]},
            indent=2, default=str))
        path = out_dir / "scorecard.md"
        path.write_text(self.markdown())
        return path
