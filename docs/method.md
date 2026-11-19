# Method: how the testing was done

This file covers how the testing was done. For what was run and when, see [runs.md](runs.md). For what was
found, see [../QA_REPORT.md](../QA_REPORT.md) and [../evidence/README.md](../evidence/README.md).

## Approach

I acted as a customer's engineer deciding whether to ship on the Models API, and judged the engineering against
the docs: status codes, error clarity, limits, timeouts and recovery, not how a voice sounds. Everything went
through the **raw API** (`requests` / `websockets`), not the SDK, because the API reference is the contract.
The docs were snapshotted on 2026-11-18 into [reference/](reference/), and every test and finding cites that
snapshot.

Smallest's own agent skills (`text-to-speech`, `speech-to-text`, `setup-api-key`) were treated as **something
under test**, not as a source of truth. That is how F3 was found.

## Three stages

| Stage | Question | Tests | Evidence |
|---|---|---|---|
| **1. Feature conformance** | Does the API do what the docs say? | `tests/tts` (formats, sample rates, voice catalogue, pronunciation dictionaries, transport parity, skill claims) and `tests/cloning` (lifecycle on both pools, upload validation), plus `scripts/explore_clone_languages.py` (cross-language clones) | [tts](../evidence/2026-11-18-tts-findings.md), [cloning](../evidence/2026-11-18-cloning-findings.md) |
| **2. Realtime reliability** | Does it hold up as a voice-agent backend? | `tests/reliability`: turn loop over one WebSocket with `context_id` streaming, barge-in, keepalive and time to first audio; concurrency against the documented limit; idle timeouts, drops and reconnects; HTTP / SSE / WebSocket playback headroom | [realtime](../evidence/2026-11-18-realtime-findings.md) |
| **3. End-to-end prototype** | Can a customer build a real product on it? | `src/smallest_qa/app` plus `tests/e2e`: a branded voice support agent across 7 journeys (onboarding, web call with barge-in, phone call, busy hour, network drop, dictionary change, offboarding). Variations: `tests/e2e_stock_voice` (stock voice, to separate engine issues from clone issues) and `tests/e2e_hindi` (Hindi / Hinglish) | [e2e](../evidence/2026-11-19-e2e-runs.md) |

## The prototype (stage 3)

The prototype answers each call like this:

1. The caller's audio goes to Pulse STT.
2. A scripted LLM streams the reply word by word, at realistic timing.
3. The reply text is streamed into a WebSocket `context_id` in groups of 3 words.
4. The cloned voice speaks the reply.

What the prototype measures and simulates:

- **Caller-side metrics:** response latency, time to first audio, and gaps for a player with a 150 ms jitter
  buffer.
- **Barge-in:** what happens when the caller interrupts.
- **Phone leg:** simulated without a phone number. The prototype encodes 8 kHz G.711 μ-law in 20 ms frames and
  checks them against carrier pacing.

The workarounds that earlier findings forced are built in: re-label uploads, trim leading silence, validate
dictionary ids, gate audio after a cancel, and detect end of speech by silence.

**Scorecard** (`app/scorecard.py`): each check has a weight. A check can be marked as a blocker, and can carry a
workaround.

| Check result | Points |
|---|---|
| Pass | full weight |
| Failure that has a workaround | half weight |
| Failure with no workaround | 0 |

The verdict is one of:

- **GO**
- **GO WITH WORKAROUNDS:** score ≥ 70% and every failed blocker has a workaround.
- **NO-GO**

## Product budget used as the SLOs

| SLO | Budget |
|---|---|
| Response latency, caller done → agent audio | ≤ 1.5 s median |
| Time to first audio, first text sent → first chunk | ≤ 400 ms median (≤ 600 ms p90 under load) |
| No audible gaps | playback headroom ≥ 0 with a 150 ms buffer |
| Barge-in: audio after cancel | ≤ 0.3 s |
| End of turn: `complete` after last audio | ≤ 1 s |
| Reconnect: drop → first audio | ≤ 2 s |
| Phone | 0 late 20 ms frames (60 ms carrier jitter buffer) |

## What counts as a finding

- **Reproducibility rule.** Stages 1 and 2 were each re-run 3 more times, about 7 minutes apart and never in
  parallel. The e2e suite ran 3 full times, plus the two variations.
  - A **finding** reproduced in every run.
  - An **observation** is real but intermittent, and is reported with its measured rate.
  - Anything seen once and never again was dropped.

  See [reproducibility](../evidence/2026-11-18-reproducibility.md).
- **Severity:**
  - High: silent wrong behaviour, or a required capability is missing.
  - Medium: the docs are wrong, or an integration needs extra work.
  - Low: an easy workaround exists.
- **Few tests, each a complex scenario.** Small cosmetic issues were left out on purpose.

## Harness

| Part | What it does |
|---|---|
| `utils/http.py` | Every REST/SSE request; a global in-flight cap (`QA_MAX_IN_FLIGHT`, default 3, max 5, per the brief) |
| `utils/live.py` | A WebSocket client with a background reader. Every frame is timestamped (ms since the socket opened) together with the server `request_id` |
| `utils/evidence.py` | Appends one redacted JSON line per request or socket to `evidence/<IST date>.jsonl` (keys, tokens, cookies and `organizationId` are removed). Test failures carry the request ids |
| `utils/retry.py` | The documented 429 backoff policy (500 ms doubling to 30 s, honours `Retry-After`) |
| `waves/stt.py` | Pulse STT. It checks intelligibility: a clip is transcribed and scored against its text, with a native catalogue voice as the baseline |

## Not tested, by choice

- **Atoms:** out of scope.
- **Load testing and security probing:** forbidden by the brief.
- **The Python SDK:** the raw API is the contract. The SDK (5.14.0, pinned in `pyproject.toml`) was only searched for a clone delete method (C1).
- **Real telephony:** no phone number was rented; the phone leg was simulated.
- **Voice quality as such:** that's ML, not engineering.
- **More than 4 concurrent requests:** the brief caps requests at about 5.
