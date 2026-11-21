# Evidence

Proof for every finding in [`QA_REPORT.md`](../QA_REPORT.md). Read in this order: the **index** below → the
**note** for a finding (what, how to reproduce, request ids) → the **raw log** line for any request id.

All runs were against `https://api.smallest.ai` / `wss://api.smallest.ai` from one take-home account,
2026-11-18 and 2026-11-19 (IST). Docs compared against: [`docs/reference/smallest-docs-2026-11-18/`](../docs/reference/).

## Summary

- **7 findings reproduced in every run.**
  - High: 2 (R1, C1)
  - Medium: 5 (F1, E1, R2, F2, F3)
- **3 withdrawn on 2026-11-21** after re-checking the docs, because the docs describe the behaviour: R5 (the 4 s
  `complete` delay is the documented `complete_backoff_ms` default), C2 (the rejected MIME labels aren't on the
  reference's list) and C5 (the docs promise no 400 for a clone on the other pool). Their notes are kept, marked
  withdrawn.
- **5 observations** are intermittent and reported with their rates: E3, E2, R6, C3, C4.
- **The end-to-end prototype** was a branded voice support agent. Its verdict was **GO WITH WORKAROUNDS** in all
  7 scored runs (83–91%).
- **The stock-voice control showed R1 is engine-wide.** It isn't specific to cloned voices.
- **Cost:** about 46k characters, 179 STT calls and 18 clones. The full run log is in
  [docs/runs.md](../docs/runs.md).

## Finding index

The verdict rule: a finding is **reproducible** only if it showed up in every run (first session + 3 re-runs).
Anything less is an **observation**, reported with its measured rate.

| ID | Severity | Finding | Rate | Note |
|---|---|---|---|---|
| **R1** | High | Barge-in can't stop a released reply: `cancel_request` drops only unreleased text; released segments (even ones that start generating after the cancel) stream in full, with no ack and no `context_id` on frames. Same on stock voices (engine-wide) | every run | [realtime](2026-11-18-realtime-findings.md#r1-barge-in-cant-stop-speech-that-is-already-released), [e2e](2026-11-19-e2e-runs.md) |
| **F1** | Medium | A deleted or never-existing pronunciation dictionary id is accepted silently (200, dictionary not applied) | every run | [tts](2026-11-18-tts-findings.md#f1-a-deleted-or-never-existing-pronunciation-dictionary-id-is-accepted-silently) |
| **C1** | High | No API to delete a voice clone: the documented route returns 410 `MODEL_DEPRECATED`, the clone stays and still speaks | every run | [cloning](2026-11-18-cloning-findings.md#c1-the-only-documented-way-to-delete-a-voice-clone-returns-410-model_deprecated) |
| **R2** | Medium | The documented 1-request TTS limit didn't trigger at up to 4 parallel requests; no 429, no rate-limit headers | every run | [realtime](2026-11-18-realtime-findings.md#r2-the-documented-concurrency-limit-didnt-trigger-at-24-concurrent-requests) |
| **F2** | Medium | 4 voices in the Pro model card don't exist in the API | every run | [tts](2026-11-18-tts-findings.md#f2-4-voices-in-the-pro-model-card-dont-exist-in-the-api) |
| **F3** | Medium | Smallest's own agent skill contradicts the API in 3 places | every run | [tts](2026-11-18-tts-findings.md#f3-smallests-official-agent-skill-contradicts-the-api-in-3-places) |
| **E1** | Medium | The WebSocket ignores the documented `output_format: "ulaw"` and silently returns 16-bit PCM (REST serves μ-law) | 4/4 e2e runs that probed it | [e2e](2026-11-19-e2e-runs.md#new-from-the-prototype) |
| E2 | Observation | Hindi first audio ~500 ms vs ~250 ms in English; response latency over the 1.5 s budget | 2/2 Hindi runs | [e2e](2026-11-19-e2e-runs.md#variation-c-hindi-support-agent-testse2e_hindi-1-clone-per-run) |
| E3 | Observation | Clone speaking Hindi: runaway generation (128 s of audio for a 76-character sentence), garbled numbers | seen once (`ec2477c6`); triggering input never re-sent | [e2e](2026-11-19-e2e-runs.md#variation-c-hindi-support-agent-testse2e_hindi-1-clone-per-run) |
| R6 | Observation | A WebSocket stream stalls 0.5–7 s right after its first chunks | 2/22 reliability streams; 2/42 e2e clone turns; 0/23 stock-voice turns | [realtime](2026-11-18-realtime-findings.md), [e2e](2026-11-19-e2e-runs.md) |
| C3 | Observation | Pro clone adds a stray sound at the start (sample begins with silence) | 2/4 clones | [cloning](2026-11-18-cloning-findings.md#c3-pro-clones-add-a-stray-sound-at-the-start-when-the-sample-starts-with-silence) |
| C4 | Observation | Cross-lingual Pro clone (Japanese) sometimes unintelligible, with a 200 | 4/18 clips | [cloning](2026-11-18-cloning-findings.md#c4-observation-cross-lingual-pro-clone-sometimes-returns-unintelligible-audio-with-a-200) |

Also reproducible but parked as low value: R3 (idle timeout closes with 1006 and no close frame), R4 (the socket
stays open after `complete`, contrary to the docs). Dropped (seen once, never again): A1–A4, C6, C7. Details:
[reproducibility](2026-11-18-reproducibility.md).

## Files

| File | What it holds |
|---|---|
| `2026-11-18-tts-findings.md` | Feature conformance: formats, sample rates, voices, pronunciation dictionaries, skill claims (F1–F3) |
| `2026-11-18-cloning-findings.md` | Instant voice cloning with the owner's own recording (C1–C5) |
| `2026-11-18-realtime-findings.md` | Voice-agent turn loop, concurrency, connection durability over WebSocket / SSE / HTTP (R1, R2, R6) |
| `2026-11-18-reproducibility.md` | The 3 re-runs of everything above, and the verdict per finding |
| `repro/feature-conformance.md`, `repro/realtime.md` | Per-run working notes behind the reproducibility verdicts |
| `2026-11-19-e2e-runs.md` | The support-agent prototype: 3 full runs, the stock-voice control and the Hindi variation (E1–E3) |
| `2026-11-18.jsonl`, `2026-11-19.jsonl` | Raw log: one JSON line per request or WebSocket session |

## Reading the raw log

Every request the harness makes appends one line to `evidence/<IST date>.jsonl` (`src/smallest_qa/utils/evidence.py`):
`ts_utc`, `ts_ist`, `run` (one id per pytest session), `test` (pytest node id), `label`, `method`, `path`,
`status`, all response `headers` (including `X-Request-Id`), timings (`ttfb_ms`, `total_ms`) and a body excerpt
(audio is summarized as format, sample rate and duration, never stored). WebSocket sessions are one line with
`event: live_socket`: every frame sent and received, timestamped in ms since the socket opened, with each
chunk's server `request_id`.

```bash
grep 7eda87b9 evidence/2026-11-19.jsonl | python -m json.tool | less   # one request id
jq -c 'select(.run=="53d78cbd") | [.label, .status]' evidence/2026-11-19.jsonl   # one run
```

Redacted: API keys and tokens (`sk_...`, `wat_...`), cookie values, and the account's `organizationId`.
Not here: audio files and the owner's voice recording (`samples/`, `out/` are git-ignored).
