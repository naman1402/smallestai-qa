"""Turn-level metrics read from WebSocket timelines, so stock-voice and clone runs are measured the same way.

A timeline is what `LiveSocket` logs as `event: live_socket`: `sent` = [{"t", "msg"}], `frames` =
[{"t", "status", "request_id", "data": {"audio_bytes"}}], times in ms since the socket opened. Frames carry
no context_id, so a turn's audio is every chunk from its first text fragment until the next turn's first
fragment (the agent speaks one turn at a time per socket).

Stall census: per turn, the worst gap between consecutive audio chunks while the caller has heard less than
WINDOW_S of audio, and whether the server already had the text to fill it: the gap is inside one request_id
(a released segment, whose text was all there) or the context was already closed. A gap > STALL_MS with the
text in hand is a stall. Gaps at a segment boundary while text is still arriving are buffering, not stalls.
"""

import json
import statistics
from pathlib import Path

STALL_MS, WINDOW_S = 300, 1.5
SHORT_OPENER = 12  # "Of course." (10 chars) is held back by the server; "You are welcome." (16) is not
TERMINAL = (".", "?", "!", "…")


def turn_census(sent: list[dict], frames: list[dict], label: str = "") -> list[dict]:
    """One row per context_id on a socket: ttfa_ms, worst early gap, stall flag, talk-over after a cancel."""
    ctx: dict[str, dict] = {}
    for s in sent:
        m = s.get("msg") or {}
        cid = m.get("context_id")
        if not cid:
            continue
        c = ctx.setdefault(cid, {"first": None, "closed": None, "cancel": None, "rate": 24000, "text": ""})
        if m.get("cancel_request"):
            c["cancel"] = s["t"]
        elif m.get("continue") is False:
            c["closed"] = s["t"]
        elif isinstance(m.get("text"), str):
            c["first"] = s["t"] if c["first"] is None else c["first"]
            c["text"] += m["text"]
            c["rate"] = m.get("sample_rate", c["rate"])
    order = sorted((c["first"], cid) for cid, c in ctx.items() if c["first"] is not None)
    chunks = [f for f in frames if f.get("status") == "chunk"]
    rows = []
    for i, (start, cid) in enumerate(order):
        c = ctx[cid]
        end = order[i + 1][0] if i + 1 < len(order) else float("inf")
        mine = [f for f in chunks if start <= f["t"] < end]
        bps = c["rate"] * 2
        played = mine if c["cancel"] is None else [f for f in mine if f["t"] <= c["cancel"]]
        heard, worst = 0.0, {"gap_ms": 0.0, "at_ms": None, "text_sent": False}
        for a, b in zip(played, played[1:], strict=False):
            heard += (a.get("data") or {}).get("audio_bytes", 0) / bps
            if heard >= WINDOW_S:
                break
            gap = b["t"] - a["t"]
            if gap > worst["gap_ms"]:
                in_hand = a.get("request_id") == b.get("request_id") or (c["closed"] is not None
                                                                         and c["closed"] <= a["t"])
                worst = {"gap_ms": round(gap, 1), "at_ms": round(a["t"] - mine[0]["t"]), "text_sent": in_hand}
        rows.append({
            "socket": label, "context_id": cid,
            "ttfa_ms": round(mine[0]["t"] - start, 1) if mine else None,
            "opener_chars": next((k + 1 for k, ch in enumerate(c["text"]) if ch in TERMINAL), len(c["text"])),
            "worst_gap_ms": worst["gap_ms"], "gap_at_ms": worst["at_ms"], "text_sent": worst["text_sent"],
            "stall": worst["text_sent"] and worst["gap_ms"] > STALL_MS,
            "talk_over_s": None if c["cancel"] is None else round(
                sum((f.get("data") or {}).get("audio_bytes", 0) for f in mine if f["t"] > c["cancel"]) / bps, 2),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    answered = [r for r in rows if r["ttfa_ms"] is not None]
    stalls = [r["worst_gap_ms"] for r in answered if r["stall"]]

    def med(rs):
        return round(statistics.median(r["ttfa_ms"] for r in rs)) if rs else None

    return {"turns": len(answered), "stalls": len(stalls), "stall_gaps_ms": stalls,
            "ttfa_median_ms": med(answered),
            "ttfa_short_opener_ms": med([r for r in answered if r["opener_chars"] <= SHORT_OPENER]),
            "ttfa_other_ms": med([r for r in answered if r["opener_chars"] > SHORT_OPENER])}


def evidence_census(evidence_dir: Path, runs: list[str]) -> dict[str, list[dict]]:
    """Census of every socket the given runs logged (event: live_socket); a run not in the evidence gets []."""
    out: dict[str, list[dict]] = {r: [] for r in runs}
    for path in sorted(evidence_dir.glob("*.jsonl")):
        with path.open() as f:
            for line in f:
                if '"live_socket"' not in line or not any(r in line for r in runs):
                    continue
                rec = json.loads(line)
                if rec.get("event") == "live_socket" and rec.get("run") in out:
                    out[rec["run"]] += turn_census(rec.get("sent", []), rec.get("frames", []), rec.get("label", ""))
    return out


# --- side-by-side table --------------------------------------------------------------------------------------
CARD_ROWS = [  # (row label, journey, check name, worst of a per-turn list) as in tests/e2e/test_support_agent.py
    ("web: response latency, median (ms)", "web call", "response latency (caller done -> agent audio), median", None),
    ("web: TTS first audio, median (ms)", "web call", "TTS first audio, median", None),
    ("web: min playback headroom (s)", "web call", "no audible gaps in agent speech", min),
    ("web: audio after cancel (R1)", "web call", "barge-in: audio still sent after cancel", None),
    ("web: `complete` after last audio (ms)", "web call",
     "end of turn signalled promptly (complete after last audio)", None),
    ("phone: late 20 ms frames, worst turn", "phone call", "no late 20 ms frames at carrier pace", max),
    ("busy: TTS first audio p90 (ms)", "busy hour", "TTS first audio under load, p90", None),
    ("busy: min playback headroom (s)", "busy hour", "no audible gaps under load", min),
]


def _fmt(v, worst=None) -> str:
    if worst and isinstance(v, list) and v and all(isinstance(x, int | float) for x in v):
        return str(worst(v))
    return "n/a" if v is None else str(v)


def _card_values(checks: list[dict], journey: str, name: str, worst) -> str:
    vals = [_fmt(c["value"], worst) for c in checks if c["journey"] == journey and c["name"] == name]
    return " / ".join(vals) if vals else "n/a"


def _census_cells(s: dict) -> list[str]:
    if not s["turns"]:
        return ["n/a"] * 4
    stalls = f"{s['stalls']}/{s['turns']}" + (f" ({', '.join(map(str, s['stall_gaps_ms']))} ms)" if s["stalls"] else "")
    return [stalls, *(_fmt(s[k]) for k in ("ttfa_median_ms", "ttfa_short_opener_ms", "ttfa_other_ms"))]


def comparison_md(stock_run: str, stock: dict, clones: dict[str, dict | None], census: dict[str, list[dict]],
                  note: str = "") -> str:
    """stock / clones[run]: scorecard dicts ({"verdict", "score", "checks"}); None = scorecard not found."""
    runs = [stock_run, *clones]
    cards = {stock_run: stock, **clones}
    sums = {r: summarize(census.get(r, [])) for r in runs}
    head = [f"`{stock_run}` stock"] + [f"`{r}` clone" for r in clones]
    lines = ["# Stock voice vs cloned voice", "", note, "", "| Metric | " + " | ".join(head) + " |",
             "|---" * (len(runs) + 1) + "|",
             "| verdict (score; journeys differ) | " + " | ".join(
                 f"{c['verdict']} ({c['score']}%)" if c else "n/a" for c in cards.values()) + " |"]
    for label, journey, name, worst in CARD_ROWS:
        lines.append(f"| {label} | " + " | ".join(
            _card_values(cards[r]["checks"], journey, name, worst) if cards[r] else "n/a" for r in runs) + " |")
    census_labels = [f"stalls > {STALL_MS} ms in first {WINDOW_S} s, text in hand", "TTFA median, all turns (ms)",
                     f"TTFA median, opener <= {SHORT_OPENER} chars (ms)", "TTFA median, other openers (ms)"]
    cells = {r: _census_cells(sums[r]) for r in runs}
    for k, label in enumerate(census_labels):
        lines.append(f"| {label} | " + " | ".join(cells[r][k] for r in runs) + " |")
    pooled = [x for r in clones for x in census.get(r, [])]
    p = summarize(pooled)
    lines += ["", f"Clone runs pooled: {p['stalls']}/{p['turns']} turns stalled; stock: "
              f"{sums[stock_run]['stalls']}/{sums[stock_run]['turns']}. Stock web values are per call (a / b / c). "
              "Census rows come from socket timelines in the evidence log (run b3ede2aa's web-call timeline was "
              "capped at 120 frames, so it has fewer turns).", ""]
    return "\n".join(lines)
