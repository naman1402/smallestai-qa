# TTS findings, 2026-11-18 (confirmed live)

- **Run:** 2026-11-18, 16:10–16:13 IST, against `https://api.smallest.ai`.
- **Raw evidence:** `evidence/2026-11-18.jsonl`. It has one JSON line per request; search it for the `x-request-id`.
- **Docs compared against:** `docs/reference/smallest-docs-2026-11-18/` (snapshot taken the same day).
- **Skill compared against:** `.agents/skills/text-to-speech` from `smallest-inc/skills`, installed 2026-11-18.
- **Reproducibility:** re-run 3 times at 19:00–19:20 IST; see `2026-11-18-reproducibility.md`.
- **Severity scale:** High = silent wrong behavior in production. Medium = docs or skill steer an integration wrong. Low = an easy workaround exists (same scale as `QA_REPORT.md`).

| ID | Finding | Severity | Status |
|---|---|---|---|
| F1 | A pronunciation dictionary ID that doesn't exist is silently ignored | High | **Permanent: 4/4 runs** |
| F2 | 4 voices in the Pro model card don't exist in the API | Medium | **Permanent: 4/4 runs** |
| F3 | Smallest's official agent skill is wrong in 4 places | Medium | **Permanent: 4/4 runs** |

Reproduce everything: `make setup`, put the key in `.env`, then run `.venv/bin/pytest tests/tts -v`. F1 and F2 fail; F3 shows as passing tests, because those tests assert the API reference and the API agrees with the reference, not the skill.

---

## F1: A deleted or never-existing pronunciation dictionary ID is accepted silently

**What happens.** `POST /waves/v1/tts` with a well-formed but nonexistent dictionary ID in `pronunciation_dicts` returns **200 with audio**. The dictionary is not applied, and there is no error or warning. Only a malformed ID is rejected (400 `Invalid pronunciation dict id`). So the API validates the ID's format, not whether the dictionary exists.

**Why a customer cares.** Dictionaries exist for brand names, product names and people's names. A dictionary deleted by a teammate, a mistyped ID, or an ID from another environment means production speech mispronounces those names with nothing in logs or responses to signal it.

**Evidence**
| Step | Request | Result | x-request-id |
|---|---|---|---|
| Create a dictionary (`Qzvx` → "quality assurance verification experiment") | `POST /waves/v1/pronunciation-dicts` | 200, `id 6afd80be94edccbabd50be5f` | `a13428a0-11f2-47d5-a201-6d67044b9433` |
| TTS without the dictionary | `POST /waves/v1/tts` pcm | 200, 84,480 B (1.76 s) | `f0f81bd9-f831-4ff9-8358-186fc046fb47` |
| TTS with the dictionary: applied | same text plus `pronunciation_dicts` | 200, 157,920 B (3.29 s) | `3b9dbc4c-c33a-4609-a79c-9cbc067f237b` |
| Delete the dictionary | `DELETE /waves/v1/pronunciation-dicts` | 200, `deleted: true` | `b8bece2c-5b51-4403-87c2-051134d04cf5` |
| **TTS with the deleted ID** | same text plus the deleted ID | **200, 98,924 B WAV (~2.0 s, so not applied)** | `d0896edc-9255-43d8-8d93-4d657a5c4295` |
| **TTS with an ID that never existed** (the docs' example ID) | `pronunciation_dicts: ["64f1234567890abcdef12345"]` | **200, WAV** | `bc0029dc-bc56-454e-8266-b095c3084b89` |
| TTS with a malformed ID | `pronunciation_dicts: ["not-a-real-id"]` | 400 `Invalid pronunciation dict id` | `9862b86a-f6cc-4020-b473-44de90865b50` |

**Expected:** 400 or 404 naming the unknown dictionary ID, the same as an unknown `voice_id` gets.

**Reproduce**
```bash
curl -s -o out.wav -w "%{http_code}\n" https://api.smallest.ai/waves/v1/tts \
  -H "Authorization: Bearer $SMALLEST_API_KEY" -H "Content-Type: application/json" \
  -d '{"text":"Please say Qzvx clearly.","voice_id":"meher","model":"lightning_v3.1_pro",
       "output_format":"wav","sample_rate":24000,"pronunciation_dicts":["64f1234567890abcdef12345"]}'
# prints 200 and writes playable audio; expected a 4xx
```
Test: `tests/tts/test_pronunciation.py::test_dictionary_applies_on_every_transport_and_stale_ids_fail`. The same test confirms that a valid dictionary does apply on REST, SSE and WebSocket.

---

## F2: 4 voices in the Pro model card don't exist in the API

**What happens.** The Lightning v3.1 Pro model card lists 208 voice IDs. 204 are in the Pro catalog. These 4 are in **neither** the Pro nor the Standard catalog, and TTS rejects them:

| Voice | Listed in the docs under | TTS result | x-request-id |
|---|---|---|---|
| `ines` | European languages: Spanish (female) | 400 `Voice 'ines' is not available on the lightning_v3.1_pro model` | `f9bcc434-3323-425b-971a-59740cd3f434` |
| `paula` | European languages: Spanish (female) | 400, same message | `46dc6a2a-4110-4183-ad4a-eb85dc29fb55` |
| `sebastian` | European languages: Spanish (male) | 400, same message | `503699c0-6cc7-4b8c-90a3-f9e19ca080d0` |
| `sara` | American: Female | 400, same message | `127b5562-44a9-433d-a668-e4fc9a896458` |

Catalogs: Pro `620d71f0-6cdf-4e91-828c-4a44a5bff174` (275 voices), Standard `8e9547a0-2ed3-44d9-af18-36492593c499` (240 voices).

**Why a customer cares.** A developer picks a voice from the model card and gets a 400. The error message is clear, but the docs are the source of the wrong ID. Spanish is hit hardest: 3 of the 6 documented Spanish voices in that table are missing.

**Expected:** the model card matches `GET /waves/v1/lightning-v3.1-pro/get_voices`, ideally generated from it.

**Reproduce**
```bash
curl -s https://api.smallest.ai/waves/v1/lightning-v3.1-pro/get_voices -H "Authorization: Bearer $SMALLEST_API_KEY" \
  | jq -r '.voices[].voiceId' | grep -xE 'ines|paula|sebastian|sara'   # prints nothing
```
Test: `tests/tts/test_voices.py::test_documented_pro_voices_exist_with_their_language`. It parses the model card in the docs snapshot and also checks each voice's language tag; all 204 present voices are tagged correctly.

---

## F3: Smallest's official agent skill contradicts the API in 4 places

**Context.** `smallest-inc/skills` is what Claude Code, Codex and Cursor load to write Smallest integrations. Whatever the skill says ends up in customer code.

| Skill says | API actually does | x-request-id |
|---|---|---|
| Pro is "English, Hindi" only | Pro synthesizes Japanese (`aria`), Tamil (`malar`) and `auto` routing (Hindi text on `meher`) | `951ed057-5693-40f9-9e6e-e6c153f14f08`, `1bd2071a-ed85-48b7-a22e-c84ca9a2c44e`, `ae82baf6-7948-4aa2-946f-41bb8ec12d3b` |
| "Always set `Accept: audio/wav`; omitting it can return an empty or unplayable response" | The same WAV comes back with and without `Accept`, as the reference says ("the server ignores it") | `dcd273c3-9520-44c6-908c-0317883b9c37` (with), `5b27bbf1-f021-473c-affe-d559a30bd4c6` (without) |
| Mismatched voice/model pairs "are not rejected" and can return wrong audio | 400 `Voice 'magnus' is not available on the lightning_v3.1_pro model` | `69d9e14d-4ea2-4f3a-aedf-c03abe897391` |
| `/waves/v1/lightning-v3.1/get_voices` returns the Standard and Pro catalogs combined | Pool-scoped: Standard has 240 voices and contains only 6 of the 275 Pro voices (the shared base-queue voices) | `8a6a9f21-639d-4124-9b93-6552ac121bce` (Standard), `6a2d3aef-cd53-4593-96fe-557bebece70a` (Pro) |

**Why a customer cares.**
- Agent-written integrations skip Pro for non-English/Hindi languages.
- They add a needless header and handle mismatched voices the wrong way.
- They build voice pickers from the wrong catalog.
- The skill also defaults every example to `lightning_v3.1`, which retires 2026-11-30 (static; no request needed). Code written from it today breaks in 12 days.

**Where the skill was right:** `output_format` `ulaw` and `alaw` work (200, `audio/basic`, 8 kHz G.711), but the API reference enum lists only pcm, mp3 and wav. That's a docs gap rather than a skill bug: `0f6e3db8-3a4d-493e-951c-6d8dc260b3dd`, `200ab9bb-e419-455a-a67b-99f18484dcee`.

**Expected:** generate the skill from the API reference, and check the two against each other in CI.

**Reproduce:** `.venv/bin/pytest tests/tts/test_skill_claims.py tests/tts/test_voices.py -v`. All pass, which shows the API follows the reference, not the skill. Compare with `.agents/skills/text-to-speech/SKILL.md` and `references/voices-languages.md`.

---

## R5: `complete` arrives about 4 s after the last audio
Every one-shot WebSocket request sends `complete` **3988 ms** after its last audio chunk (default `complete_backoff_ms` is 4000). With `complete_backoff_ms: 0` the gap is 0.1 ms. Every doc sample waits for `complete`, so a voice agent built from them adds about 4 s per turn: `e32e77b9-41cb-4664-8cee-4b3e93b35043` vs `8c990a3a-0c5a-4687-b09b-3a079043546a`.

## Checked and working as documented
- Every format and rate tested returned the right container, header rate and Content-Type: pcm, wav and mp3 at 8, 16, 24 and 44.1 kHz.
- A minimal request defaults to pcm at 44100 Hz.
- REST, SSE and WebSocket return matching audio for the same text.
- Word timestamps match the input words and fall inside the audio.
- `context_id` continuations come back as one release with a stable session.
