# QA report: Smallest AI Models API

| | |
|---|---|
| **Scope** | Lightning TTS (REST, SSE, WebSocket), instant voice cloning, and Pulse STT where it supports them: the core of any voice agent built on Smallest. Atoms is out of scope |
| **Method** | Feature conformance → realtime reliability → an end-to-end prototype (a branded voice support agent, scored go/no-go). Each stage was run once, then re-run 3 times. The prototype ran 7 scored times in 3 variations. See [docs/method.md](docs/method.md) and [docs/runs.md](docs/runs.md) |
| **Evidence** | [evidence/README.md](evidence/README.md) has the full trail for each finding: note, request ids, raw log. Times are IST (UTC+5:30), dates 2026-11-18/19 |
| **Time spent** | About 16–20 hours |

## Verdict

**GO WITH WORKAROUNDS**, on one condition. Products that must delete cloned voices on request (consent
withdrawal, erasure, end of contract) should treat it as **NO-GO** until C1 is fixed.

This was the verdict in all 7 scored e2e runs, at 83–91%. Each run needed 5 client-side workarounds, and
offboarding was manual. Details: [e2e runs](evidence/2026-11-19-e2e-runs.md).

## Findings at a glance

A finding is listed only if it showed up in **every** run that exercised it. Anything less is an observation
(below). SLOs are a customer's product budget: [method.md](docs/method.md#product-budget-used-as-the-slos).

| ID | Sev. | Finding |
|---|---|---|
| [R1](#r1--high--barge-in-cant-stop-speech-thats-already-released) | High | Barge-in can't stop speech that's already released |
| [F1](#f1--high--unknown-pronunciation-dictionary-ids-are-silently-accepted) | High | Unknown pronunciation dictionary ids are silently accepted |
| [C1](#c1--high--voice-clones-cant-be-deleted-through-the-api) | High | Voice clones can't be deleted through the API |
| [R2](#r2--medium--the-documented-concurrency-limit-isnt-enforced) | Medium | The documented concurrency limit isn't enforced |
| [C2](#c2--medium--valid-wav-uploads-are-rejected-by-mime-label) | Medium | Valid WAV uploads are rejected by MIME label |
| [C5](#c5--medium--the-clone-must-match-its-pool-rule-isnt-enforced) | Medium | The "clone must match its pool" rule isn't enforced |
| [F2](#f2--medium--4-voices-on-the-pro-model-card-dont-exist) | Medium | 4 voices on the Pro model card don't exist |
| [F3](#f3--medium--smallests-agent-skill-contradicts-the-api) | Medium | Smallest's agent skill contradicts the API |
| [R5](#r5--low--complete-arrives-4-s-after-the-speech-ends) | Low | `complete` arrives 4 s after the speech ends |
| [E1](#e1--low--the-websocket-ignores-output_format-ulaw) | Low | The WebSocket ignores `output_format: "ulaw"` |

Severity: **High** = silent wrong behaviour, or a required capability is missing. **Medium** = the docs are
wrong, or an integration needs extra work. **Low** = an easy workaround exists.

Commands assume `make setup` and a key in `.env`. Cost and clone rules: [AGENTS.md](AGENTS.md#before-you-run-anything-cost-and-safety).

## Findings

### R1 · High · Barge-in can't stop speech that's already released
- **Expected → observed:** `cancel_request` should stop the context's speech → it drops only text the server hasn't started on. Audio already released keeps streaming, and no frame acknowledges the cut.
- **Customer impact:** the agent talks over a caller who interrupted it. SLO: talk-over under 0.3 s.
- **Runs:** 4/4 reliability sessions (11.8–14.7 s streamed after the cancel). 4/4 English e2e runs on a clone and on a stock voice (0.8–3.4 s), so it's engine-wide. Hindi: 5.6 s in one run and 0.16 s in the other (one barge-in each).
- **Evidence:** `7117cfcf-c16c-49e9-acc3-3ec156e3e6ae` (11-18 18:33), `3b778853-4b6b-4328-97ab-e80f2a1a53ea` (e2e, 11-19 02:20) · [realtime note](evidence/2026-11-18-realtime-findings.md#r1-barge-in-cant-stop-speech-that-is-already-released) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability/test_agent_turns.py -k barge_in -v`

### F1 · High · Unknown pronunciation dictionary ids are silently accepted
- **Expected → observed:** an unknown dictionary id should get a 4xx → a deleted or made-up id gets **200** with audio, and no dictionary is applied.
- **Customer impact:** brand names are mispronounced after a dictionary is deleted or an id is mistyped, and nothing errors. SLO: invalid input gets a 4xx.
- **Runs:** 4/4 sessions; 4/4 e2e runs (the dictionary-change journey).
- **Evidence:** `d0896edc-9255-43d8-8d93-4d657a5c4295` (deleted id, 11-18 16:11), `bc0029dc-bc56-454e-8266-b095c3084b89` (made-up id, 16:13), `b3852712-ccf4-4429-aef0-ed671c2c5297` (e2e, 11-19 02:21) · [tts note](evidence/2026-11-18-tts-findings.md#f1-a-deleted-or-never-existing-pronunciation-dictionary-id-is-accepted-silently) · `.venv/bin/pytest tests/tts/test_pronunciation.py -v`

### C1 · High · Voice clones can't be deleted through the API
- **Expected → observed:** the documented delete (`DELETE /waves/v1/lightning-large`) should remove the clone → **410 `MODEL_DEPRECATED`**. The clone stays listed and still speaks. The API reference and SDK have no other delete, and the error points to a speech endpoint on a model that retires 2026-11-30.
- **Customer impact:** an erasure request needs a person in the dashboard, with no API and no audit trail. SLO: deletion through the API.
- **Runs:** 4/4 sessions; 4/4 e2e offboarding journeys. All 12 logged delete attempts returned 410.
- **Evidence:** `e33b55f1-d11a-4ede-ad7e-5164b1831f54` (11-18 17:02), `bb1b2305-d297-4597-a905-67969666db5c` (e2e, 11-19 02:21) · [cloning note](evidence/2026-11-18-cloning-findings.md#c1-the-only-documented-way-to-delete-a-voice-clone-returns-410-model_deprecated) · `.venv/bin/pytest tests/cloning/test_lifecycle.py -v` (creates 2 clones)

### R2 · Medium · The documented concurrency limit isn't enforced
- **Expected → observed:** 1 TTS request per account, with a 429 for extras → 2 HTTP, HTTP + WebSocket, and 2 WebSocket requests were all served. There were no 429s and no rate-limit headers. We tested up to 4 at once (the brief's cap), so the real limit is unknown.
- **Customer impact:** capacity gets planned on a number that isn't true, the real limit can't be discovered, and 429 handling is never exercised. SLO: limits are enforced and discoverable.
- **Runs:** 4/4 sessions. The e2e busy-hour journey (3 concurrent callers) also got 0 429s in every run.
- **Evidence:** `9e3ece90-9cc7-4bd1-aa87-f0e92fdd06b6` and `a013e842-4951-428a-82da-98eb47014b78`, both 200 at the same moment (11-18 18:30) · [realtime note](evidence/2026-11-18-realtime-findings.md#r2-the-documented-concurrency-limit-didnt-trigger-at-24-concurrent-requests) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability/test_concurrency.py -v`

### C2 · Medium · Valid WAV uploads are rejected by MIME label
- **Expected → observed:** a valid `.wav` should be accepted → **400 "Invalid file type."** for `audio/x-wav`, `audio/vnd.wave` and `application/octet-stream`. Only `audio/wav` and `audio/wave` work.
- **Customer impact:** the first upload from a browser or Python's `mimetypes` fails, and the message gives no hint.
- **Runs:** 4/4 sessions. Every e2e clone run hit it, and the product retries as `audio/wav`.
- **Evidence:** `6ed50388-bb38-4474-9dc6-5746f2928a37` (11-18 17:02), `d206175e-67c9-4d81-aa04-ab50214b71cd` (e2e, 11-19 02:20) · [cloning note](evidence/2026-11-18-cloning-findings.md#c2-clone-upload-rejects-valid-wav-files-based-on-the-declared-mime-type) · `.venv/bin/pytest tests/cloning/test_validation.py -v`

### C5 · Medium · The "clone must match its pool" rule isn't enforced
- **Expected → observed:** the docs say a clone on the other model pool gets a 400 → **200** with intelligible speech, in both directions.
- **Customer impact:** a documented rule can't be relied on, and it's unclear what the 2026-11-30 retirement of `lightning_v3.1` will break.
- **Runs:** 4/4 sessions (STT similarity 0.90–1.00); also every e2e run, as an informational check.
- **Evidence:** `bc458d27-2880-494c-b6df-a4e177be8132` (base clone on Pro), `9c0e56c5-831a-4929-afff-7e8b9afa9bfd` (Pro clone on base), both 11-18 17:18 · [cloning note](evidence/2026-11-18-cloning-findings.md#c5-the-documented-clone-must-match-its-pool-rule-is-not-enforced) · `.venv/bin/pytest tests/cloning/test_lifecycle.py -v` (creates 2 clones)

### F2 · Medium · 4 voices on the Pro model card don't exist
- **Expected → observed:** every voice on the model card should exist → `ines`, `paula`, `sebastian` and `sara` get 400. That's 3 of the card's 6 Spanish voices.
- **Customer impact:** a voice picked from the docs fails.
- **Runs:** 4/4 sessions, with the same 4 of 208 missing each time.
- **Evidence:** `f9bcc434-3323-425b-971a-59740cd3f434` (`ines`), `127b5562-44a9-433d-a668-e4fc9a896458` (`sara`), both 11-18 16:13 · [tts note](evidence/2026-11-18-tts-findings.md#f2-4-voices-in-the-pro-model-card-dont-exist-in-the-api) · `.venv/bin/pytest tests/tts/test_voices.py -v`

### F3 · Medium · Smallest's agent skill contradicts the API
- **Expected → observed:** the official `smallest-inc/skills` should match the API → it's wrong in 4 places: Pro languages, the `Accept` header, mismatched voices, and the voice catalog. It also defaults to `lightning_v3.1`, which retires 2026-11-30.
- **Customer impact:** integrations written by coding agents (Claude Code, Codex, Cursor) start out wrong.
- **Runs:** 4/4 sessions. The tests pass, because they assert what the API actually does, which is what the skill gets wrong.
- **Evidence:** `69d9e14d-4ea2-4f3a-aedf-c03abe897391` (a mismatched voice gets 400; the skill says it doesn't, 11-18 16:11) · [tts note](evidence/2026-11-18-tts-findings.md#f3-smallests-official-agent-skill-contradicts-the-api-in-4-places) · `.venv/bin/pytest tests/tts/test_skill_claims.py -v`

### R5 · Low · `complete` arrives 4 s after the speech ends
- **Expected → observed:** `complete` should mark the end of speech → it arrives 3.5–4.1 s after the last audio (the default `complete_backoff_ms` is 4000). With `complete_backoff_ms: 0` the gap is 0.1 ms.
- **Customer impact:** every docs sample waits for `complete`, so an agent built from them adds about 4 s per turn. SLO: under 1 s. Workaround: lower the backoff, or detect silence.
- **Runs:** 4/4 sessions; every e2e turn on a clone and on a stock voice, so it's engine-wide.
- **Evidence:** `e32e77b9-41cb-4664-8cee-4b3e93b35043` (default) vs `8c990a3a-0c5a-4687-b09b-3a079043546a` (backoff 0), both 11-18 16:12 · [tts note](evidence/2026-11-18-tts-findings.md#also-observed-as-documented) · `.venv/bin/pytest tests/tts/test_websocket.py -k complete_backoff -v`

### E1 · Low · The WebSocket ignores `output_format: "ulaw"`
- **Expected → observed:** μ-law (as REST serves it) → 16-bit PCM with no error. The μ-law/PCM byte ratio was 0.94–1.07, where μ-law would be about 0.5.
- **Customer impact:** a phone integration that trusts the setting sends PCM to the carrier as μ-law, which plays as noise. Workaround: request 8 kHz PCM and encode G.711 locally (0 late frames in every run).
- **Runs:** 4/4 runs with a phone leg (3 on a clone, 1 on a stock voice).
- **Evidence:** `94c068ca-d545-411a-87f6-34065a796699` (11-19 02:21), `c9914b61-c4e1-4ed4-ae42-56b07b5f3973` (stock voice, 11:32) · [e2e note](evidence/2026-11-19-e2e-runs.md#new-from-the-prototype) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_stock_voice -v -s` (0 clones)

## Observations

These are real but intermittent, so they're reported with the measured rate.

| ID | What | Rate | Evidence |
|---|---|---|---|
| E3 | A clone speaking Hindi ran away: 128 s of audio for a 76-character sentence, with garbled numbers | 1 of 3 Hindi runs | [e2e](evidence/2026-11-19-e2e-runs.md#variation-c-hindi-support-agent-testse2e_hindi-1-clone-per-run) · `68519717-c779-412b-b76a-dc309d69a175` (11-19 04:03) |
| E2 | Hindi first audio took about 500 ms (English about 250 ms), so response latency went over 1.5 s. Only 6 turns were measured | 2 of 2 Hindi runs | same |
| R6 | A WebSocket stream stalls 0.5–7 s right after its first chunk | 4 of 67 (2/40 reliability streams, 2/27 e2e clone turns); 0 of 23 turns in the stock-voice e2e run | [realtime](evidence/2026-11-18-realtime-findings.md#r6-observation-not-reproduced-in-re-runs-a-websocket-stream-sometimes-stalls-right-after-its-first-chunks), [e2e](evidence/2026-11-19-e2e-runs.md#new-from-the-prototype) |
| C3 | A Pro clone adds a stray opening syllable when the sample starts with silence | 2 of 4 clones | [cloning](evidence/2026-11-18-cloning-findings.md#c3-pro-clones-add-a-stray-sound-at-the-start-when-the-sample-starts-with-silence) |
| C4 | A cross-lingual Pro clone (Japanese) is sometimes unintelligible, yet still returns 200 | 4 of 18 clips | [cloning](evidence/2026-11-18-cloning-findings.md#c4-observation-cross-lingual-pro-clone-sometimes-returns-unintelligible-audio-with-a-200) |

## Docs gaps

All checked against the [docs snapshot](docs/reference/smallest-docs-2026-11-18/):

- `cancel_request`, the barge-in control, appears only on the Continuations page. It's missing from the WebSocket schema, and the schema also has no error frame.
- The latency figures disagree with each other: "~100 ms first chunk", "~200 ms TTFB", and "200 ms at 40 concurrent requests".
- `ulaw` and `alaw` work on REST but are missing from the format enum.
- The Hindi danda `।` ends a sentence for buffering (first audio in 178 ms), but the docs list only `. ? ! …`.
- The C1 error message points to an endpoint that retires on 2026-11-30.

## What's done well

- **Streaming is fast.** WebSocket first audio has a median of 137 ms and SSE 224 ms. The prototype answers
  callers in 1.1–1.4 s.
- **Output is correct everywhere.** Every format and sample rate tested is correct, and all three transports
  return the same audio.
- **Failures are handled cleanly.** Timeouts match the docs to the second, bad WebSocket messages get an error
  frame and the socket keeps working, and a reconnect resumes audio in about 0.5 s.
- **It holds up under small load.** 3 concurrent callers caused no degradation, and the 8 kHz phone leg had
  no late frames.
- **Hindi and Hinglish content comes out right:** numbers, ₹ amounts and Indian-format dates.

## Top 3 fixes

1. **R1:** make `cancel_request` stop audio that's already released, and acknowledge the cut. Every voice agent
   interrupts, the problem is engine-wide, and the only workaround still streams the audio (and likely bills it).
2. **C1:** ship a working, documented clone delete API. Without it, compliance-bound customers get a NO-GO,
   and the docs already promise this endpoint.
3. **F1:** reject unknown dictionary ids with a 4xx. This is silent wrong output that customers can't detect,
   and the API already does this lookup for voices.

## Security (private field)

No vulnerability was found, and no probing was done (per the brief). Two findings sit near the line:

- **C1:** voice biometric data can't be erased through the API.
- **R2:** without enforced limits or limit headers, there's a cost and abuse exposure (not probed).
