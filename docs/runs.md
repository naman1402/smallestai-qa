# Runs: what was run, when, and what it found

Every live session against `api.smallest.ai`, in order. Times are IST (UTC+5:30). The **run id** is the
`"run"` field in `evidence/<date>.jsonl`. Filter one session with:

```bash
jq -c 'select(.run=="RUN_ID")' evidence/2026-11-18.jsonl
```

Why the runs were set up this way is in [method.md](method.md). The proof for each finding is indexed in
[../evidence/README.md](../evidence/README.md).

## How to re-run

```bash
make setup && $EDITOR .env                       # SMALLEST_API_KEY=sk_...
.venv/bin/pytest tests/tts -v                    # feature conformance: TTS
.venv/bin/pytest tests/cloning -v                # feature conformance: cloning (needs samples/my_voice.wav; creates 2 clones)
QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability -v -m "not slow"   # realtime reliability
QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e -v -s                      # e2e prototype (1 clone)
QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_stock_voice -v -s          # stock-voice control (0 clones)
QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_hindi -v -s                # Hindi agent (1 clone)
```

The cost of each suite and the safety rules are in [../AGENTS.md](../AGENTS.md#before-you-run-anything-cost-and-safety).
Clones can't be deleted through the API (C1), so delete them in the dashboard afterwards.

## 2026-11-18: feature conformance

| Time | Run id | What | Found |
|---|---|---|---|
| 16:11–16:13 | `c8515a37`, `57c69606` | `tests/tts` plus manual checks | F1, F2, F3 → [tts note](../evidence/2026-11-18-tts-findings.md) |
| 17:01–17:07 | `b9a14f66`, `af47befc`, `780c7f75` | Cloning upload and delete, then the delete re-checked with the docs' curl | C1, C2 → [cloning note](../evidence/2026-11-18-cloning-findings.md) |
| 17:13–17:21 | `f0a4469e`, `95b92c76`, `723b7239`, `3a74774e`, `d4000e06` | `scripts/explore_clone_languages.py`: a clone speaking other languages, Japanese repeats, wrong-pool use, a leading-silence A/B | C3, C4, C5 |
| 17:17–17:18 | `94fc7b11` | `tests/cloning`: full lifecycle on both pools | C1, C2, C5 confirmed |

## 2026-11-18: realtime reliability

| Time | Run id | What | Found |
|---|---|---|---|
| 18:29–18:40 | `c6989a02`, `b6cea09e`, `f6f7886c`, `65e47cbe` (+ raw checks `eacb400b`, `fd08cde3`, `29f0842b`) | `tests/reliability`: turn loop, barge-in, concurrency, timeouts, transports | R1, R2, R6 → [realtime note](../evidence/2026-11-18-realtime-findings.md) |
| 18:53–18:57 | `f30d6564` | Slow idle-timeout tests | Timeouts match the docs; R3 |

## 2026-11-18: 3 re-runs of everything above

| Time | Run ids | Result |
|---|---|---|
| 19:00–19:18 | TTS `378e15fc`, `068e5679`, `f6073382`; cloning `0d143700`, `796b95a5`, `466040f8`; extra clones `5a488b8b`, `bbd031dc`, `8f506989` | F1, F2, F3, C1, C2, C5 every run; C3 in 2 of 4 clones; C4 in 4 of 18 clips |
| 19:22–19:39 | Realtime `36237db5`, `9fba16e6`, `750f3162` | R1, R2 every run; R6 in 0 of 18 (2 of 22 overall) |

Verdicts: [reproducibility](../evidence/2026-11-18-reproducibility.md). Per-run notes:
[repro/](../evidence/repro/).

## 2026-11-19: end-to-end prototype

| Time | Run id | Suite | Verdict | Found |
|---|---|---|---|---|
| 00:40–00:42 | `b3ede2aa` | `tests/e2e` | GO WITH WORKAROUNDS, 83.6% | C2, R1, R5, F1, C1 hit by the product; E1; one R6 stall |
| 00:43 | `6d70a3f9` | `tests/e2e` (partial: a local disk-quota error broke 3 journeys) | GO WITH WORKAROUNDS, 83.3% | Same as above for the 4 journeys that ran |
| 02:18–02:21 | `f0d2f3cf`, `53d78cbd` | `tests/e2e` | GO WITH WORKAROUNDS, 88.5% each | Same set, every run |
| 04:01–04:03 | `ec2477c6` | `tests/e2e_hindi` (an accidental run, stopped after about 2 min) | – | **E3:** runaway generation, 128 s of audio for 76 characters |
| 11:30–11:32 | `9694c27b` | `tests/e2e_stock_voice` | GO WITH WORKAROUNDS, 91.1% | R1 and R5 also on a stock voice, so engine-wide; 0 of 23 stalls |
| 11:32–11:34 | `e704b21f` | `tests/e2e_hindi` | GO WITH WORKAROUNDS, 90.4% | E2 (slow first audio); no runaway |
| 12:31–12:32 | `05580081` | `tests/e2e_hindi` | GO WITH WORKAROUNDS, 87.7% | E2 again; no runaway (E3 is now 1 of 3) |

Details: [e2e note](../evidence/2026-11-19-e2e-runs.md).

## Totals

| | |
|---|---|
| Characters synthesized | about 46,000 (32.5k on 2026-11-18, 13.8k on 2026-11-19) |
| STT calls | 179 |
| Voice clones created | 18. The API can't delete them; each has to be deleted by hand in the dashboard |
| Concurrency | never more than 4 requests or sockets at once |
