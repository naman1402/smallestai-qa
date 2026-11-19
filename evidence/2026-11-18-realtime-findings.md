# Realtime findings (agent turn loop, concurrency, connection durability), 2026-11-18

- **Run:** 2026-11-18, about 18:20–18:45 IST; re-run 3 times 19:22–19:42 IST (results: `2026-11-18-reproducibility.md`), against `wss://api.smallest.ai/waves/v1/tts/live` and `https://api.smallest.ai/waves/v1/tts`.
- **Raw evidence:** `evidence/2026-11-18.jsonl`. WebSocket scenarios are logged as `event: live_socket` with every frame timestamped in ms since the socket opened, plus each chunk's server `request_id`.
- **Tests:** `tests/reliability/`. Harness: `src/smallest_qa/utils/live.py` (timestamped live socket) and `utils/retry.py` (the documented 429 backoff policy).
- **Docs compared against:** `docs/reference/smallest-docs-2026-11-18/`.
- **Load:** stayed inside the brief. At most 4 sockets or requests at once, short phrases, about 2,500 characters synthesized in total.

| ID | Finding | Severity | Status |
|---|---|---|---|
| R1 | Barge-in can't stop speech: `cancel_request` drops only unreleased text, and the reply already released keeps streaming for seconds | High | **Permanent: 5/5 runs** (2 first session + 3 re-runs) |
| R6 | A WebSocket stream sometimes stalls right after its first chunks (7.1 s and 1.7 s of silence), so a fast first chunk is followed by dead air; SSE had no audible stall | Observation | **Intermittent:** 2 of 22 WebSocket streams, both in the first session; 0 of 18 in the re-runs |
| R2 | The documented limit of 1 TTS request per account (429 for extras) never triggered at 2–4 concurrent requests, and no header exposes the real limit | Medium | **Permanent: 4/4 runs** |

Reproduce: `QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/reliability -v -m "not slow"`. R1 fails in `test_barge_in…`; R2 fails in `test_second_http…`, `test_one_slot…` and `test_extra_websocket…`; R6 fails (intermittently) in `test_transports.py::test_stream_keeps_ahead_of_playback[ws]`.

---

## R1: Barge-in can't stop speech that is already released

**Docs:** `cancel_request` appears only on the Continuations page ("discards whatever is currently buffered for the context without speaking it, but does not end the context itself"). It is not in the WebSocket message schema, and nothing describes audio that is already being generated.

**Scenario:** like a voice agent. Stream a 5-sentence reply in a `context_id`. Once audio is playing, add a fragment with no sentence end, which stays buffered. At about 0.4 s into playback, send `{"context_id": …, "cancel_request": true}`.

| Run | Cancel sent | Reply audio after the cancel | Segments that *started* after the cancel | Buffered fragment | Ack frame |
|---|---|---|---|---|---|
| 1 | 583 ms | 14.7 s total, all played | `1e3574ea-98b9-4d94-9962-7ead3a68e9aa` started +1497 ms (6.4 s of audio) | n/a | none |
| 2 | 585 ms | 13.9 s after the cancel (14.0 s total) | `7117cfcf-c16c-49e9-acc3-3ec156e3e6ae` started +1075 ms (6.2 s of audio) | **dropped** (total unchanged) | none |
| Control | text sent with no sentence end, cancelled 0.5 s later | 0 s | none | **dropped** | none |

**What this means.**
- Cancel works only on text the server hasn't started on.
- An LLM reply is released sentence by sentence almost at once, so in practice a cancel stops nothing the caller is about to hear. Even segments that begin generating 1–1.5 s *after* the cancel are streamed in full.
- No acknowledgement frame tells the client where the cut happened.
- The only ways to stop are to drop audio on the client (it keeps arriving, and is presumably billed) or to close the socket.

**Why a customer cares.** Barge-in is the defining feature of a voice agent. Here the agent keeps sending up to 14 s of a reply the caller has already interrupted. Every integration has to build its own audio gate, and the docs don't warn about it.

**Expected:** `cancel_request` stops generation and streaming for the context, including released segments; an ack frame marks the cut-off; and the field is in the reference schema.

---

## R6 (observation, not reproduced in re-runs): A WebSocket stream sometimes stalls right after its first chunks

> **Re-run result:** 0 stalls in 18 WebSocket and 18 SSE streams across 3 re-runs (19:22–19:42 IST). Overall: 2 of 22 WebSocket streams. It does not meet the report's reproduce-every-run bar; see `2026-11-18-reproducibility.md`.

**Method** (`tests/reliability/test_transports.py::test_stream_keeps_ahead_of_playback`): a 14 s reply as one one-shot request. Simulate a player that starts at the first chunk with a 150 ms jitter buffer. At every chunk, compare the audio received so far with the audio already played. Negative headroom is silence the listener hears.

| Transport | Run | First audio | Biggest gap between chunks | Audio received before the gap | Worst headroom | x-request-id |
|---|---|---|---|---|---|---|
| WebSocket | harness | 141 ms | **7067 ms** | 0.24 s | **−6.96 s** | `fa468191-418a-4a1d-b5bc-a2adc451c276` |
| WebSocket | raw client 0 | 155 ms | **1688 ms** | 0.13 s | **−1.44 s** | `2671a348-f715-4509-94ff-53128baf3afc` |
| WebSocket | raw client 1 | 159 ms | 701 ms (final 128-byte chunk) | 14.2 s | −0.08 s | `f3578379-04a9-4659-b65f-fddbc6ba7afb` |
| WebSocket | raw client 2 | 220 ms | 3222 ms (final chunk) | 14.2 s | +0.14 s | `42d37889-111b-4d12-9a0d-4c36965e423c` |
| SSE | harness | 511 ms | 274 ms | – | ≥ 0 | `underrun-sse` record |
| SSE | 0 | 365 ms | 1730 ms | 2.0 s (after event 12) | −0.11 s | `7d418cf8-2720-46b2-bf9e-0b3e39111ed1` |
| SSE | 1 | 330 ms | 335 ms | – | +0.05 s | `16f9ee8e-ff58-4c9c-9317-6ded17f7a302` |
| SSE | 2 | 796 ms | 726 ms (final event) | – | +0.09 s | `6953602a-d0cc-4417-85dc-40af3eaaa603` |

**What happens.**
- In 2 of 4 WebSocket runs, the first one or two chunks (0.1–0.25 s of audio) arrive in about 150 ms. Then nothing comes for 1.7–7.1 s, and the rest of the reply arrives in a burst. The listener hears a syllable, then silence.
- The first-audio number (141–155 ms) looks excellent, which hides the problem.
- The plain-client runs show it isn't our harness.
- SSE's first audio is slower (330–800 ms), but it arrives in a bigger burst, and no SSE run left the player more than about 0.1 s short.
- Two WebSocket runs also held the tiny final chunk back 0.7–3.2 s. That's harmless for playback, but it delays the end of the stream.

**Why a customer cares.** WebSocket is the transport the docs recommend for voice agents. A stall right after the first syllable is the worst place for one: the agent starts talking, then goes silent mid-word for up to 7 s. Making playback safe needs a multi-second jitter buffer, which throws away the low-latency advantage. "Time to first audio" alone is the wrong success metric for this API.

**Limitations:** 4 runs per transport, from one client location (geo-routed region not pinned), one voice and one text. It's intermittent; the 3× re-run before the report will firm up the rate.

---

## R2: The documented concurrency limit didn't trigger at 2–4 concurrent requests

**Docs** (`concurrency-and-limits`):
- "Only 1 Text-to-Speech request can be actively processed at a time per account", across sync, SSE and WebSocket.
- A second HTTP request gets "429 Too Many Requests".
- Extra WebSocket requests "will be rejected with an error".
- About 4 parallel conversations per unit.

| Scenario | Documented | Observed | x-request-id |
|---|---|---|---|
| 2 HTTP requests at the same moment | one 200, one 429 | **both 200** (1.6 s and 2.3 s) | `9e3ece90-9cc7-4bd1-aa87-f0e92fdd06b6`, `a013e842-4951-428a-82da-98eb47014b78` |
| HTTP request while a WebSocket request is generating | 429 | **200** | HTTP `e92e8dda-a0a2-4ca9-844d-5def0473caa5`; WS segment `ff2ea2af-c40e-4a00-bc2e-9ba952dcee82` |
| 2nd WebSocket request while the 1st is generating | rejected with an error | **served**, first audio in 295 ms | `d04cf316-ae91-4831-a1e0-96bf23b75e00` |
| 3 callers using the documented backoff | some 429s, then recovery | all 200 on the first try | `live_socket` and `retry` records `backoff-caller-*` |
| 4 conversations × 3 turns, staggered | ~4 is a "rough estimate" | 12 of 12 turns served | `conv-*` records |

No response carried a rate-limit or concurrency header.

**Why a customer cares.**
- Capacity planning is built on these numbers. Teams build queues and tell product "4 calls per unit" based on the documented limit of 1.
- The real limit can't be discovered through the API. When a customer does hit it, they meet behavior that has never been documented correctly.
- The docs' own async sample, which writes error JSON to `.wav` on a 429, only looks safe because the limit didn't trigger.

**Limitation:** we didn't go above 4 concurrent requests (brief cap of about 5), so the real limit is unknown. The documented one did not apply at 2–4.

**Expected:** document the actual per-plan TTS concurrency, and expose it, for example with `X-RateLimit-*` / `X-Concurrency-*` headers.

---

## Time to first audio by transport (5 sequential samples each, short sentence)

| Transport | Median | Min–max | Docs claim |
|---|---|---|---|
| HTTP (first body byte; the whole file is generated first) | 1286 ms | 720–2987 ms | none (the docs say use sync "when total latency doesn't matter") |
| SSE (first audio event) | 277 ms | 256–323 ms | "~100 ms" / "~200 ms" |
| WebSocket (first chunk) | 206 ms | 147–216 ms | "~100 ms" / "~200 ms" |

Records: `ttfa-http-*`, `ttfa-sse-*`, `ttfa-ws-*`.

---

## Worked as documented
- **Idle timeouts match the docs to the second:** the default closed at 59.97 s ("Connection timed out after 60 seconds of inactivity"), `?timeout=500` was capped at 179.98 s, and `?timeout=5` closed at 4.98 s.
- **Time to first audio within a conversation** (context on one socket): 171 / 316 / 317 ms per turn.
- **SSE under contention:** two SSE streams at once both completed intact (done terminator, full length), and an SSE request during a WebSocket generation completed, as did the WebSocket stream (`sse-pair-*`, `sse-during-ws`, `sse-vs-ws`).
- **SSE client disconnect:** closing an SSE stream after 3 events doesn't affect the next request, which streams normally.
- **SSE bad requests fail before streaming:** an unknown voice or blank text gets a 400 with a JSON error (`application/json`), the same as REST (`fbef021d-8bbd-4231-a23a-3d2282d350c2`).
- `ping`, `keepalive`, `keep_alive` and `keep-alive` all get `pong` and reset the idle timer. A client pinging every 2 s kept a 5 s-timeout socket alive through a turn and 12 s of silence.
- Malformed JSON, a missing `voice_id` and an unknown message type each get an error frame (`Invalid input data`, the latter two with a precise reason), and the socket keeps working.
- Reconnecting after a timeout is served immediately (first audio in 128 ms).
- A client that drops mid-stream doesn't block the next connection.

## Seen but kept out of this evidence
- Idle-timeout closes carry no WebSocket close frame (clients see 1006).
- The socket stays open after `complete`, although the docs say it closes.
- `complete` arrives about 4 s after the last chunk on every turn, inside continuations too.
- The idle timer counts only client messages, so a short `?timeout` can close a socket mid-turn before `complete`.
