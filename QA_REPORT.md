# QA report: Smallest AI Models API

| | |
|---|---|
| **Scope** | Lightning TTS (REST, SSE, WebSocket) and instant voice cloning: the core of any voice agent built on Smallest. Atoms is out of scope. Pulse STT was used only as a measuring tool (intelligibility checks, caller turns) and was not tested against its own docs. Its rate limit (5 × 429 after 26 calls in 36 s, no `Retry-After`, 2026-11-18 17:13 IST) slowed those measurements and wasn't investigated further |
| **Method** | Feature conformance → realtime reliability → an end-to-end prototype (a branded voice support agent, scored go/no-go). Each stage was run once, then re-run 3 times. The prototype ran 7 scored times in 3 variations. See [docs/method.md](docs/method.md) and [docs/runs.md](docs/runs.md) |
| **Evidence** | [evidence/README.md](evidence/README.md) has the full trail for each finding: note, request ids, raw log. Times are IST (UTC+5:30), dates 2026-11-18/19 |

## Verdict

**GO WITH WORKAROUNDS**, on one condition. Products that must delete cloned voices on request (consent
withdrawal, erasure, end of contract) should treat it as **NO-GO** until C1 is fixed.

This was the verdict in all 7 scored e2e runs, at 83–91%. Each run needed client-side workarounds, and the
clone runs needed manual offboarding (C1). Details: [e2e runs](evidence/2026-11-19-e2e-runs.md).

## Findings at a glance

A finding is listed only if it showed up in **every** feature-conformance and reliability session that exercised
it (the first session plus 3 re-runs); e2e runs are supporting evidence. Anything less is an observation
(below). Each finding was re-checked against the [docs snapshot](docs/reference/smallest-docs-2026-11-18/):
behaviour the docs describe is not reported as a defect. SLOs are a customer's product budget:
[method.md](docs/method.md#product-budget-used-as-the-slos).

| ID | Sev. | Finding |
|---|---|---|
| [R1](#r1--high--barge-in-cant-stop-a-reply-thats-already-released) | High | Barge-in can't stop a reply that's already released |
| [F1](#f1--high--unknown-pronunciation-dictionary-ids-are-silently-accepted) | High | Unknown pronunciation dictionary ids are silently accepted |
| [C1](#c1--high--voice-clones-cant-be-deleted-through-the-api) | High | Voice clones can't be deleted through the API |
| [E1](#e1--medium--the-websocket-silently-ignores-output_format-ulaw) | Medium | The WebSocket silently ignores `output_format: "ulaw"` |
| [R2](#r2--medium--the-documented-1-request-tts-limit-didnt-trigger) | Medium | The documented 1-request TTS limit didn't trigger |
| [F2](#f2--medium--4-voices-on-the-pro-model-card-dont-exist) | Medium | 4 voices on the Pro model card don't exist |
| [F3](#f3--medium--smallests-agent-skill-contradicts-the-api) | Medium | Smallest's agent skill contradicts the API |

Severity: **High** = silent wrong behaviour, or a required capability is missing. **Medium** = the docs are
wrong, an integration needs extra work, or a silent failure has a cheap client-side workaround. **Low** = an
easy workaround exists.

Commands assume `make setup` and a key in `.env`. Cost and clone rules: [AGENTS.md](AGENTS.md#before-you-run-anything-cost-and-safety).

## Findings

### R1 · High · Barge-in can't stop a reply that's already released
- **Expected → observed:** the Continuations page, the only one that mentions it, says `cancel_request` "discards whatever is currently buffered for the context without speaking it". A voice agent sends it when the caller interrupts → it drops only text still waiting for a sentence end. Sentences already released keep being generated and streamed in full, including segments whose generation starts 1.1–1.5 s *after* the cancel. 11.5–13.9 s of the cancelled reply's audio arrives within about 2.4 s of the cancel. No frame acknowledges the cancel, and audio frames carry no `context_id`.
- **Customer impact:** to stop the agent talking, the client must throw away about 12 s of audio on its own. Nothing marks where the cut is, and with no `context_id` on frames (each released segment has its own server `request_id`) a socket carrying more than one context can't tell which chunks to drop. The server also generates audio nobody hears; whether it's billed wasn't checked. SLO: audio of a cancelled context delivered after the cancel ≤ 0.3 s, or an ack frame that marks the cut.
- **Runs:** 5/5 reliability barge-in runs on 2026-11-18: 12.6, 13.9, 12.2, 12.0 and 11.5 s of audio after the cancel (recomputed from the raw logs: bytes of the cancelled context received after the cancel, 24 kHz 16-bit). 4/4 English e2e runs on a clone and on a stock voice (0.8–3.4 s), so it's engine-wide. Hindi e2e: 5.6 s in one run and 0.16 s in the other (one barge-in each).
- **Evidence:** `7117cfcf-c16c-49e9-acc3-3ec156e3e6ae` (a segment that started 1.07 s after the cancel and streamed 6.2 s of audio, 2026-11-18 18:33 IST), `5417f71b-83bf-45da-bf31-7e4361821876` (e2e, kept streaming after the cancel, 2026-11-19 02:20 IST) · [realtime note](evidence/2026-11-18-realtime-findings.md#r1-barge-in-cant-stop-speech-that-is-already-released) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability/test_agent_turns.py -k barge_in -v`

### F1 · High · Unknown pronunciation dictionary ids are silently accepted
- **Expected → observed:** an unknown dictionary id should get a 4xx (the dictionaries guide lists "Dictionary not found" as an error to troubleshoot) → a deleted or made-up id gets **200** with audio, and no dictionary is applied.
- **Customer impact:** brand names are mispronounced after a dictionary is deleted or an id is mistyped, and nothing errors. SLO: invalid input gets a 4xx.
- **Runs:** 4/4 sessions; 4/4 e2e runs (the dictionary-change journey).
- **Evidence:** `d0896edc-9255-43d8-8d93-4d657a5c4295` (deleted id, 2026-11-18 16:11 IST), `bc0029dc-bc56-454e-8266-b095c3084b89` (made-up id, 16:13 IST), `b3852712-ccf4-4429-aef0-ed671c2c5297` (e2e, 2026-11-19 02:21 IST) · [tts note](evidence/2026-11-18-tts-findings.md#f1-a-deleted-or-never-existing-pronunciation-dictionary-id-is-accepted-silently) · `.venv/bin/pytest tests/tts/test_pronunciation.py -v`

### C1 · High · Voice clones can't be deleted through the API
- **Expected → observed:** the documented delete (`DELETE /waves/v1/lightning-large`, "deletes any voice clone on your organization") should remove the clone → **410 `MODEL_DEPRECATED`**. The clone stays listed and still speaks. The API reference and SDK have no other delete, and the error points to a speech endpoint on a model that retires 2026-11-30.
- **Customer impact:** an erasure request needs a person in the dashboard, with no API and no audit trail. SLO: deletion through the API.
- **Runs:** 4/4 sessions; 4/4 e2e offboarding journeys. All 12 logged delete attempts returned 410.
- **Evidence:** `e33b55f1-d11a-4ede-ad7e-5164b1831f54` (2026-11-18 17:02 IST), `bb1b2305-d297-4597-a905-67969666db5c` (e2e, 2026-11-19 02:21 IST) · [cloning note](evidence/2026-11-18-cloning-findings.md#c1-the-only-documented-way-to-delete-a-voice-clone-returns-410-model_deprecated) · `.venv/bin/pytest tests/cloning/test_lifecycle.py -v` (creates 2 clones)

### E1 · Medium · The WebSocket silently ignores `output_format: "ulaw"`
- **Expected → observed:** the streaming guide's parameter table for the WebSocket and SSE lists `output_format`: "`pcm`, `mp3`, `wav`, `ulaw`, or `alaw`" ([streaming.md](docs/reference/smallest-docs-2026-11-18/models__text-to-speech__streaming.md), line 373), and REST honours it: `ulaw` returns `audio/basic`, 8-bit G.711 at 8 kHz. → On the WebSocket, a `ulaw` request comes back as 16-bit PCM, with no error and no warning frame (every frame of all 4 probe sockets was logged: only `chunk` and `complete`).
- **How it was measured:** on one socket, the same sentence ("Your delivery is confirmed.", 8 kHz, same voice) was requested once as `pcm` and once as `ulaw`. μ-law is 1 byte per sample and PCM is 2, so real μ-law should be about half the PCM size. The ulaw/pcm byte ratio was 0.99, 1.05 and 0.94 on a clone and 1.07 on a stock voice. Read as μ-law, the 32,026-byte "ulaw" reply would be 4.0 s of audio for four words. Read as 16-bit PCM it's 2.0 s, the same as the `pcm` reply (33,948 bytes, 2.1 s). For comparison, REST `ulaw` returned 31,105 bytes (3.9 s) of `audio/basic` for a 71-character sentence. Limitation: this is inferred from byte counts and durations; the WebSocket bytes weren't decoded and played. SSE `ulaw` wasn't tested.
- **Customer impact:** phone integrations take 8 kHz μ-law in 20 ms frames. One that trusts the parameter forwards 16-bit PCM labelled as μ-law, and the caller hears loud noise; it also sends twice the bytes. Nothing errors, so it surfaces only on a live call. SLO: a documented parameter is honoured, or rejected with an error. Workaround: request 8 kHz PCM and encode G.711 on the client (the prototype did this, with 0 late 20 ms frames in every run). The WebSocket API schema doesn't list `output_format` at all, so the two WebSocket references disagree.
- **Runs:** 4/4 e2e runs that probed it (3 on a clone, 1 on a stock voice).
- **Evidence:** ulaw replies `2be85e30-1fe6-4e3d-a021-b6dad2484b7f` (2026-11-19 00:41 IST, ratio 0.99), `a3e808bb-30c7-4d7a-944f-4b99719ed10f` (02:19 IST, 1.05), `94c068ca-d545-411a-87f6-34065a796699` (02:21 IST, 0.94), `c9914b61-c4e1-4ed4-ae42-56b07b5f3973` (stock voice, 11:32 IST, 1.07); REST controls `0f6e3db8-3a4d-493e-951c-6d8dc260b3dd` (`ulaw`) and `200ab9bb-e419-455a-a67b-99f18484dcee` (`alaw`), 2026-11-18 16:11 IST · [e2e note](evidence/2026-11-19-e2e-runs.md#new-from-the-prototype) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e_stock_voice -v -s` (0 clones)

### R2 · Medium · The documented 1-request TTS limit didn't trigger
- **Expected → observed:** the Concurrency and Limits page says "Only 1 Text-to-Speech request can be actively processed at a time per account", and a second HTTP request gets a 429 → 2 HTTP, HTTP + WebSocket, and 2 WebSocket requests in parallel were all served with 200, with no 429 and no rate-limit headers. We stopped at 4 at once (the brief's cap), so the real limit is unknown. The plans page's "20 concurrent calls" for Pay As You Go sits with the agent-call pricing, so it's unclear whether it applies to TTS.
- **Customer impact:** capacity gets planned on a number that didn't hold, and the API exposes nothing (no limit headers) to discover the real one. SLO: the documented limit holds, or the docs state the real one.
- **Runs:** 4/4 sessions. The e2e busy-hour journey (3 concurrent callers) also got 0 TTS 429s in every run.
- **Evidence:** `9e3ece90-9cc7-4bd1-aa87-f0e92fdd06b6` and `a013e842-4951-428a-82da-98eb47014b78`, both 200 at the same moment (2026-11-18 18:30 IST) · [realtime note](evidence/2026-11-18-realtime-findings.md#r2-the-documented-concurrency-limit-didnt-trigger-at-24-concurrent-requests) · `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability/test_concurrency.py -v`

### F2 · Medium · 4 voices on the Pro model card don't exist
- **Expected → observed:** every voice on the model card should exist → `ines`, `paula`, `sebastian` and `sara` get 400. That's 3 of the card's 6 Spanish voices.
- **Customer impact:** a voice picked from the docs fails.
- **Runs:** 4/4 sessions, with the same 4 of 208 missing each time.
- **Evidence:** `f9bcc434-3323-425b-971a-59740cd3f434` (`ines`), `127b5562-44a9-433d-a668-e4fc9a896458` (`sara`), both 2026-11-18 16:13 IST · [tts note](evidence/2026-11-18-tts-findings.md#f2-4-voices-in-the-pro-model-card-dont-exist-in-the-api) · `.venv/bin/pytest tests/tts/test_voices.py -v`

### F3 · Medium · Smallest's agent skill contradicts the API
- **Expected → observed:** the official `smallest-inc/skills` should match the API → it's wrong in 3 places: Pro languages ("English, Hindi" only; Pro synthesized Japanese and Tamil), the `Accept` header ("always set it"; the API returns the same WAV without it, as the reference says), and the voice catalog (a "union" of both pools; the API's lists are pool-scoped). It also defaults to `lightning_v3.1`, which retires 2026-11-30.
- **Customer impact:** integrations written by coding agents (Claude Code, Codex, Cursor) start out wrong.
- **Runs:** 4/4 sessions. The tests pass, because they assert what the API actually does, which is what the skill gets wrong.
- **Evidence:** `951ed057-5693-40f9-9e6e-e6c153f14f08` (Japanese on Pro), `5b27bbf1-f021-473c-affe-d559a30bd4c6` (no `Accept`, same WAV), `8a6a9f21-639d-4124-9b93-6552ac121bce` / `6a2d3aef-cd53-4593-96fe-557bebece70a` (Standard / Pro catalogs), all 2026-11-18 IST · [tts note](evidence/2026-11-18-tts-findings.md#f3-smallests-official-agent-skill-contradicts-the-api-in-3-places) · `.venv/bin/pytest tests/tts/test_skill_claims.py -v`

## Observations

These are real but intermittent, so they're reported with the measured rate.

| ID | What | Rate | Evidence |
|---|---|---|---|
| E3 | A clone speaking Hindi ran away: 128 s of audio for a 76-character sentence, with garbled numbers | 1 of 3 Hindi runs (the one that was stopped early, unscored) | [e2e](evidence/2026-11-19-e2e-runs.md#variation-c-hindi-support-agent-testse2e_hindi-1-clone-per-run) · `68519717-c779-412b-b76a-dc309d69a175` (2026-11-19 04:03 IST) |
| E2 | Hindi first audio took about 500 ms (English about 250 ms), so response latency went over 1.5 s. Only 6 turns were measured | 2 of 2 Hindi runs | same |
| R6 | A WebSocket stream stalls 0.5–7 s right after its first chunk | 2 of 22 WebSocket streams (reliability); 2 of 42 e2e turns on a clone; 0 of 23 on a stock voice | [realtime](evidence/2026-11-18-realtime-findings.md#r6-observation-not-reproduced-in-re-runs-a-websocket-stream-sometimes-stalls-right-after-its-first-chunks), [e2e](evidence/2026-11-19-e2e-runs.md#new-from-the-prototype) |
| C3 | A Pro clone adds a stray opening syllable when the sample starts with silence | 2 of 4 clones | [cloning](evidence/2026-11-18-cloning-findings.md#c3-pro-clones-add-a-stray-sound-at-the-start-when-the-sample-starts-with-silence) |
| C4 | A cross-lingual Pro clone (Japanese) is sometimes unintelligible, yet still returns 200 | 4 of 18 clips | [cloning](evidence/2026-11-18-cloning-findings.md#c4-observation-cross-lingual-pro-clone-sometimes-returns-unintelligible-audio-with-a-200) |

## Docs gaps

All checked against the [docs snapshot](docs/reference/smallest-docs-2026-11-18/):

- `cancel_request`, the barge-in control, appears only on the Continuations page and is missing from the
  WebSocket schema. The schema's response `status` enum lists only `chunk`, `word_timestamp` and `complete`,
  although the same page shows `status: "error"` frames.
- The latency figures disagree with each other: "~100 ms first chunk", "~200 ms TTFB", and "200 ms at 40
  concurrent requests".
- Pages disagree on voice/model mismatches. The API reference says a mismatched pair returns 400, the Pro model
  card says "the API does not currently reject mismatched pairings", and the voices page says ids "only work
  with" their model. Observed: a catalog voice on the other pool gets 400; a clone on the other pool gets 200
  with speech.
- The cloning guide says `.wav` is supported, while the API reference accepts only the labels `audio/wav` and
  `audio/wave`. A WAV labelled `audio/x-wav` or `audio/vnd.wave` (Python's `mimetypes` returns one of these, depending on
  the version) gets 400 "Invalid file type.", which doesn't name the accepted types.
- The Hindi danda `।` ends a sentence for buffering (first audio in 178 ms), but the docs list only `. ? ! …`.
- The C1 error message points to an endpoint that retires on 2026-11-30.

## What's done well

- **Streaming is fast.** WebSocket first audio has a median of 137 ms and SSE 224 ms. The prototype answers
  callers in 1.1–1.4 s.
- **REST output is correct.** Every format and sample rate tested over REST came back as requested, and the
  three transports return the same PCM audio for the same request (the WebSocket `ulaw` exception is E1).
- **Failures are handled cleanly.** Timeouts match the docs to the second, bad WebSocket messages get an error
  frame and the socket keeps working, and a reconnect resumes audio in about 0.5 s.
- **It holds up under small load.** 3 concurrent callers caused no degradation, and the 8 kHz phone leg had
  no late frames.
- **Hindi and Hinglish content comes out right:** numbers, ₹ amounts and Indian-format dates.

## Top 3 fixes

1. **R1:** make `cancel_request` stop released segments too, and acknowledge the cut with a frame that names
   the context. Every voice agent interrupts, the problem is engine-wide, and today the client has to discard
   about 12 s of audio per interruption with nothing marking where the cut is.
2. **C1:** ship a working, documented clone delete API. Without it, compliance-bound customers get a NO-GO,
   and the docs already promise this endpoint.
3. **F1:** reject unknown dictionary ids with a 4xx. This is silent wrong output that customers can't detect,
   and the API already does this lookup for voices.

## Security (private field)

No vulnerability was found, and no probing was done (per the brief). Two findings sit near the line:

- **C1:** voice biometric data can't be erased through the API.
- **R2:** without enforced limits or limit headers, there's a cost and abuse exposure (not probed).
