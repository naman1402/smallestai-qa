# Reproducibility of all findings: 3 extra runs per stage, 2026-11-18

- **What this file is:** after the first session (16:10–18:45 IST), every feature-conformance and realtime check was run 3 more times, about 7 minutes apart.
  - Feature conformance (output, voices, pronunciation, skill claims, cloning): 19:00–19:20 IST.
  - Realtime reliability (realtime): 19:22–19:42 IST.
- **One stage at a time,** never in parallel, so neither could cause or hide the other's concurrency results. At most 4 requests or sockets were in flight.
- **Raw evidence:** `evidence/2026-11-18.jsonl`. Per-run working notes are in `evidence/repro/feature-conformance.md` and `evidence/repro/realtime.md` .
- **Verdict rule:** a finding goes in the QA report only if it reproduced in **every** run: the first session plus all 3 re-runs. Intermittent issues are listed with their measured rate. Anything seen once and never again is dropped.

## Permanent: reproduced in 4 of 4 sessions (these go in the QA report)

| ID | Finding | Severity | Re-runs | Re-run evidence (x-request-id) |
|---|---|---|---|---|
| **R1** | Barge-in can't stop speech: `cancel_request` drops only unreleased text, and an already-released reply keeps streaming with no ack | High | 3/3 | 11.8–12.2 s of audio after the cancel; a reply segment started 0.97–1.07 s after it: `f811b3af-29d6-4f97-acb0-c52b2b67a9e6`, `e4271e3b-5e0f-4268-a1fb-7d604633080b`, `dfb8ef19-6af0-454b-a338-5953eb60c44e` |
| **F1** | A deleted or never-existing pronunciation dictionary ID is accepted silently (200 with audio) | High | 3/3 | `8f9893ec-e099-43d3-810a-c6457975203c`, `328a8ede-2aa6-4d7e-852f-254b6b16d75a`, `4823246a-f59e-40a6-90da-34a8b7371066` |
| **C1** | Clones can't be deleted through the API: the documented route returns 410 `MODEL_DEPRECATED` and the clone stays | High | 3/3 | `31d798d7-a62d-489d-82a5-32204dc4ee5e`, `08ab3d80-4ee6-4c2c-a296-a6cdd002220d`, `b9b01fb4-c7ce-4477-99f3-e2075d510a1c` |
| **R2** | The documented limit of 1 request per account with a 429 is not enforced: HTTP+HTTP, HTTP+WebSocket and WebSocket+WebSocket are all served, there are never any 429s, and no rate-limit headers | Medium | 3/3 | the second WebSocket request was served in 138–167 ms each run; 12/12 conversation turns served each run (`evidence/repro/realtime.md`) |
| **C2** | Valid WAV uploads labelled `audio/x-wav` or `audio/vnd.wave` are rejected with 400 "Invalid file type." | Medium | 3/3 | every upload that got a response was a 400 (see A2 for 2 uploads that got none) |
| **C5** | The documented "clone must match its pool, mismatch = 400" rule isn't enforced: a Pro clone speaks on `lightning_v3.1` | Medium | 3/3 | 200, STT similarity 0.90 / 0.98 / 1.00: `d687896b-…`, `b4a7f645-…`, `28d924c2-…` (full ids in `evidence/repro/feature-conformance.md`) |
| **F2** | 4 voices in the Pro model card (`ines`, `paula`, `sebastian`, `sara`) don't exist in the API | Medium | 3/3 | the same 4 of 208 missing every run |
| **F3** | Smallest's agent skill contradicts the API in 4 places; the API follows its reference | Medium | 3/3 | all `test_skill_claims` pass every run; mismatched voice gets 400: `5d0fe9f7-…`, `f932d677-…`, `6aa0048c-…` |

Also permanent, but parked as lower value and not in the report: R3 (idle-timeout close has no close frame, 1006), R4 (the socket stays open after `complete`, contrary to the docs), R5 (`complete` arrives 3.9–4.1 s after the last chunk on every turn; 9/9 turns) was parked here, then **promoted to a Low finding** after the e2e prototype showed it adds about 4 s per turn to an agent built from the docs' samples, on stock voices too ([e2e](2026-11-19-e2e-runs.md)).

## Intermittent: real, but not every run (report as observations with their rate)

| ID | Finding | Rate measured | Notes |
|---|---|---|---|
| C3 | Pro clone adds a stray opening sound ("Two…", "Hello…") | **2 of 4 clones affected.** The first-session clone: 4/8 clips in a controlled run. Run 1's clone: 4/5. The run 2 and run 3 clones: 0/5 each | It seems to depend on the clone, not the request. Each clone either has it or doesn't. The original A/B (trimming the leading silence removed it, 0/8) still holds for that clone. The stray clips start with a 0.17–0.30 s sound followed by 0.3–0.85 s of silence |
| C4 | Pro clone in Japanese is sometimes unintelligible, with a 200 | **4 of 18 clips (22%)**: 2/9 in the first session, 2/9 across the re-runs (0, 2, 0) | A stable rate across sessions. Run 2's bad clip produced almost the same Korean-sounding transcript as the first session's: `71c98c19-3e2f-424a-ab12-0d88ea695a5b` |
| R6 | WebSocket stream stalls right after the first chunks | **2 of 22 WebSocket streams**, both in the first session around 18:38 IST; **0 of 18** in the re-runs. SSE 0 of 22 | Not reproducible this evening. Too few samples to give a rate, and it may depend on server load (time to first audio was clearly faster in the re-runs, below). Dropped from the report's findings; mention only as an observation if at all |

## Seen once, not reproduced (dropped)
- **A1:** a one-shot WebSocket request never got `complete` within 10 s, and its first chunk came after 1421 ms (`2e8d66b6-6cad-4d5b-9656-010b0611b811`, feature-conformance re-run 1). 1 of more than 30 WebSocket requests in the re-runs.
- **A2:** two clone uploads got no HTTP response (the connection was closed or hit an SSL EOF). Could be the local network; there's no request id.
- **A3 / A4:** two cloned clips with an ambiguous STT reading ("Is my clone voice…", "Yes, is my cloned voice…"). They could be STT misses. Listen to `out/repro/run2/c3_pro_1.wav` and `out/repro/run3/c3_pro_2.wav`.

## Correction to the first-session write-up
In R1 run 1, segment `b0f12194-d873-41d4-8442-0285be9acafa` ("started +4135 ms after the cancel") was the **resume** reply. It started 195 ms after "Sorry, go ahead." was sent at 4522 ms. The latest a *cancelled-reply* segment started is **+1.5 s** after the cancel (`1e3574ea-98b9-4d94-9962-7ead3a68e9aa`). R1 still holds. Fixed in `2026-11-18-realtime-findings.md`.

## Time to first audio (median of 5 sequential short requests)

| Session | HTTP (whole file) | SSE | WebSocket |
|---|---|---|---|
| First session (18:3x IST) | 1286 ms | 277 ms | 206 ms |
| Re-run 1 / 2 / 3 | 634 / 588 / 567 ms | 224 / 211 / 228 ms | 140 / 133 / 153 ms |
| All 15 re-run samples | **579 ms** | **224 ms** | **137 ms** |

The docs claim "~100 ms first chunk" and "~200 ms TTFB". WebSocket is close to those claims, and SSE is about 1.1–1.4× the 200 ms figure. All transports were faster in the evening re-runs than in the first session.

## Clones created by the re-runs (the API can't delete them, C1): delete in the dashboard
- `voice_9EtJpn840B`
- `voice_MUFo6l1O8A`
- `voice_MP5POBtYFB`

## Cost of the re-runs
- **Text-to-speech:** about 22,600 characters (feature conformance about 5,300, realtime about 17,300).
- **Speech-to-text:** 24 calls (about 65 s of audio).
- **Clones:** 3 created.
