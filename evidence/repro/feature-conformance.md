# Feature-conformance repeatability check: 3 runs, 2026-11-18 evening (IST)

> Working notes from the 3 re-runs. Paths under `out/` (per-run logs, clips) and the one-off `scripts/repro_*` helpers were local and are not in the repo; every request id quoted here can be found in `evidence/2026-11-18.jsonl`.

- **Runs:** run 1 19:00–19:06, run 2 19:08–19:13, run 3 19:15–19:20 IST. All against `https://api.smallest.ai`, sequential, at most one request in flight.
- **Per run:**
  1. `pytest tests/tts`
  2. `pytest tests/cloning/test_validation.py`
  3. `scripts/repro_cloning.py --run N`, which creates ONE Pro clone from the first 12 s of `samples/my_voice.wav` as recorded (mono 24 kHz WAV).
- **Raw evidence:** `evidence/2026-11-18.jsonl`. Evidence run ids are listed per run below.
- **Per-run artifacts:** `out/repro/run<N>/`: pytest logs, `ids_*.txt` (request ids per test), `results.json`, clips.
- **Helper scripts (new):** `scripts/repro_cloning.py`, `scripts/repro_evidence_ids.py`.
- **C3/C4 scoring:**
  - Each clip is transcribed with Pulse STT, with calls at least 3.5 s apart.
  - **C3 stray:** the STT heard word(s) before "This".
  - **C4 unintelligible:** similarity to the input below 0.3.

## Summary

| Finding | Reproduced | Verdict | Evidence (one line) |
|---|---|---|---|
| F1 deleted dictionary id accepted (200) | 3/3 | **permanent** | stale-id TTS 200 in each run: `8f9893ec-e099-43d3-810a-c6457975203c`, `328a8ede-2aa6-4d7e-852f-254b6b16d75a`, `4823246a-f59e-40a6-90da-34a8b7371066` |
| F2 `ines`, `paula`, `sebastian`, `sara` missing from the Pro catalog | 3/3 | **permanent** | same 4/208 missing each run; Pro catalog `201057ee-777f-41af-b6ac-3767e5d6a144` / `623dd293-0e05-49ba-9c63-b03e91b87d86` / `d434ea54-13fc-4a28-aceb-0ecc93782215` |
| F3 API follows the reference, not the skill (incl. ulaw/alaw 200) | 3/3 | **permanent** | all 5 `test_skill_claims` tests pass each run; mismatch 400 `5d0fe9f7-…`, `f932d677-…`, `6aa0048c-…` |
| C1 no API delete (410 `MODEL_DEPRECATED`, clone still listed) | 3/3 | **permanent** | 410 `31d798d7-a62d-489d-82a5-32204dc4ee5e`, `08ab3d80-4ee6-4c2c-a296-a6cdd002220d`, `b9b01fb4-c7ce-4477-99f3-e2075d510a1c` |
| C2 `audio/x-wav` and `audio/vnd.wave` rejected 400 `Invalid file type.` | 3/3 (both labels, each run) | **permanent** | see the run tables. In runs 1 and 2, one test request died at the transport level (A2) and was retried once by hand; the retry gave the 400. |
| C3 stray opening sound on a Pro clone (sample as recorded) | 1/3 runs (3/12 clips; 4/12 counting one ambiguous clip) | **intermittent** | run 1: 3/4 "Two, this is…" `03df5781-…`, `fffc555e-…`, `9afe3c2b-…`; runs 2–3: 0/4 (run 3 has one ambiguous clip, "Yes, is my…", `a722109b-…`) |
| C5 Pro clone on `lightning_v3.1` gets 200 with correct speech (docs: 400) | 3/3 | **permanent** | 200 with similarity 0.90 / 0.98 / 1.00: `d687896b-…`, `b4a7f645-…`, `28d924c2-…` |
| C4 Japanese on the Pro clone is sometimes unintelligible, with a 200 | 1/3 runs (2/9 clips) | **intermittent** (same 2/9 rate as the first session) | run 2: 2/3 bad, `71c98c19-3e2f-424a-ab12-0d88ea695a5b` (sim 0.00), `f6555724-bf02-4536-8b91-cfd513eafbc8` (sim 0.18) |
| (3.3, realtime note) WS `complete` arrives about 4 s after the last chunk by default | 2/3 ran normally (3896, 3988 ms; with backoff 0: 0.0, 0.1 ms) | as before when it ran normally; see A1 | run 1: `complete` never arrived (A1) |

## NEW anomalies (not in the existing findings)

- **A1. WebSocket one-shot request never sent `complete`** (run 1 only, 1/3; the test failed).
  - **What happened:** `test_one_shot_request_waits_for_complete_backoff`, default backoff, request id `2e8d66b6-6cad-4d5b-9656-010b0611b811`, session `252bf709-72a6-4df7-b456-92e40050785a`, 19:02:24 IST.
    - 7 chunks (53,632 B, about 1.12 s of PCM), then nothing for 10 s, so the client idle timeout ended it.
    - First chunk took 1,421 ms. The other runs took 133–242 ms and produced 59,760–77,040 B with 10–12 chunks.
  - **What it could mean:** a stalled or truncated generation with no error and no `complete`.
  - **What it could also be:** a 10 s idle window is our harness's choice. The server may have sent `complete` later. We cannot tell from this data.
  - **Same session, other sockets:** 5 others in run 1 all got `complete`.
- **A2. Transport-level drops on `POST /waves/v1/voice-cloning`** (2 of 7 clone uploads this evening; 0 of 18 earlier today; no other endpoint dropped).
  - **Run 1, `audio/x-wav`, 19:03:56 IST:** `RemoteDisconnected('Remote end closed connection without response')` after 181 ms.
  - **Run 2, `audio/vnd.wave`, 19:11:02 IST:** `SSLError UNEXPECTED_EOF_WHILE_READING` after 1,158 ms.
  - Neither got an HTTP response, so there is no x-request-id. Both are in `evidence/2026-11-18.jsonl` (runs `0d143700`, `796b95a5`, field `error`).
  - **Cannot be attributed:** this could be the local network, proxy or TLS path rather than the API. Both hit the multipart upload endpoint. Each retried request got the normal 400.
- **A3. First word missing in a Pro-clone clip** (run 2, C3 #1, `ee402aa7-bff8-448f-a183-ecf54849e1a8`, STT `8b3111ab-6593-40ee-b17f-a9317f362c67`).
  - **What happened:** the STT heard "Is my clone voice speaking?". The clip is 1.81 s, while its siblings are 2.13–2.28 s, and it has no leading gap.
  - **What it suggests:** "This" was dropped or swallowed, not prefixed.
  - **Caveat:** it could be an STT miss. Only listening can confirm.
- **A4. Ambiguous C3 clip** (run 3, C3 #2, `a722109b-73cf-4aba-9440-7b116d7c458a`, STT `e4b8226a-ae39-49cc-bffc-0e7e39004e86`).
  - **What happened:** the STT heard "Yes, is my cloned voice speaking?". The clip is 2.56 s, about 0.5 s longer than its siblings. There is a 0.30 s burst, then a short gap.
  - **What it suggests:** possibly the C3 stray sound merged with "This".
  - **How it is counted:** my script did not count it as C3, because "This" is absent. Shown as the ambiguous "4/12" above.
- **Observation for C4:** run 2's bad clip transcribes to almost the same Korean string as the first session ("커키노와 굳이 한니 현반생과 슈파십" vs the earlier "고소와 굳이 한니 현반생과로 싶"). The failure mode looks repeatable rather than random noise.
- **Observation for C3:** each run used a new clone from the same sample. Strays clustered in one clone:
  - Run 1's clone was 4/5 (C3 3/4, plus its C5 clip "Hello, this is…").
  - The run 2 and run 3 clones were 0/5 each (0–1/5 counting A4).
  - This suggests the stray sound may vary per clone (clone creation), not just per request. With 5 clips per clone, that is a hypothesis, not a result.
- **Onset measurement:** stray clips (run 1 C3 1/2/4 and run 1 C5) show the signature measured locally with ffmpeg `silencedetect` (-35 dB): a 0.17–0.30 s sound at t=0, then 0.31–0.85 s of silence before "This". Clean clips show no gap that long.

## Run 1 (TTS evidence run `378e15fc`, clone-validation `0d143700` + manual retry `48639ca3`, repro `5a488b8b`)

### Test outcomes
| Test | Result |
|---|---|
| test_pronunciation::test_dictionary_applies_on_every_transport_and_stale_ids_fail | FAIL (F1) |
| test_rest::test_output_is_what_was_asked_for | pass |
| test_rest::test_minimal_request_uses_documented_defaults | pass |
| test_skill_claims (ulaw, alaw, accept header, catalog scope, mismatch) | 5 pass |
| test_transport_parity::test_same_text_gives_same_audio_on_every_transport | pass |
| test_voices::test_documented_pro_voices_exist_with_their_language | FAIL (F2) |
| test_voices::test_documented_language_synthesizes_with_its_catalog_voice[ja, ta, auto] | 3 pass |
| test_websocket::test_one_shot_request_waits_for_complete_backoff | **FAIL (NEW, A1)** |
| test_websocket::test_word_timestamps_align_with_text_and_audio | pass |
| test_websocket::test_continuation_speaks_fragments_as_one_generation | pass |
| cloning test_validation[audio/x-wav] | FAIL: transport error (A2), no response; manual retry → 400 `Invalid file type.` `cd0a61b5-cfac-458f-ae86-18909b47d144` |
| cloning test_validation[audio/vnd.wave] | FAIL (C2): 400 `Invalid file type.` `f62b1922-6f57-4b28-a6c3-f6f0bce37ce4` |

### Findings
| Finding | Observed | x-request-id |
|---|---|---|
| F1 | dictionary created, applied, deleted; stale id → 200 WAV 90,284 B | create `d594089b-9585-4a75-8ac8-ee9bbb8f2e35`, delete `b78eea1f-f9dd-474b-ae56-382dbb3b28a5`, stale `8f9893ec-e099-43d3-810a-c6457975203c` |
| F2 | 4/208 missing: ines, paula, sara, sebastian; 0 mis-tagged | Pro catalog `201057ee-777f-41af-b6ac-3767e5d6a144`, `04f80639-161a-49ae-a87f-dd4580cac35e` |
| F3 | ulaw 200, alaw 200, Accept on/off same, catalogs pool-scoped, mismatch 400 | `e994b29d-9264-42fc-b72e-cfc0f8c06467`, `0962c2b5-627d-489e-bb20-fc8c0071db21`, `abb56a73-5b3e-4ad8-b1a0-0c01c0442e8e`/`8b50ec31-13c6-4971-8aef-00b99112c787`, `621b091a-b02a-476c-a3c3-1dea3e0ddf74`, `5d0fe9f7-5bf4-49e2-b25c-6361bc3eca12` |
| 3.3 WS | default: no `complete` (A1); backoff-0 case not reached (test stopped at first assert) | `2e8d66b6-6cad-4d5b-9656-010b0611b811` |
| Clone create | 200 `voice_9EtJpn840B`, `modelIds ['lightning-v3.1-pro']` | `3b1102c7-a412-495d-a26f-22aef661ff5c` |
| C3 | **3/4 stray**: "Two, this is my clone voice speaking." ×2, "Two. This is…" ×1; 1 clean | TTS/STT: `03df5781-6425-419c-b26a-d78c5b94af96`/`29deee50-afc8-4fbd-b561-0ae57d87f2ec`, `fffc555e-1803-4e32-8d0c-2da672bfa644`/`2a2e3955-7d96-4e87-8746-8fb8f323df01`, `145faffc-f647-4970-92b7-d450b78f173d`/`d325bf02-a1a7-4ec5-88f0-d6228b3c8ee3` (clean), `9afe3c2b-6341-42f5-aee1-2f3b04da66c1`/`230d1a24-9157-40a3-8de6-1aae6397121a` |
| C5 | 200, "Hello, this is my clone voice speaking." sim 0.90 (correct speech plus a C3-style stray "Hello") | `d687896b-cfa4-4222-9b1f-16596671d09b` / STT `c8475b91-0aca-4b00-a325-56c18fa79d91` |
| C4 | 0/3 unintelligible (sim 0.77, 0.73, 0.74; the first word 空港行き misheard each time) | `5c18a458-12fa-4c83-bddf-d687d8ea522e`/`3e311591-54fe-414b-a84a-9558daaa866e`, `ff638ce4-8467-4a12-8a81-3e3d8bf78c48`/`0ab85138-6c63-4824-9d5c-fe36962850ed`, `df8f5c28-7e62-42d1-988e-4afb4c1fe3a9`/`daaa4ab7-56a5-4822-b423-561d4781d42a` |
| C1 | DELETE 410 `MODEL_DEPRECATED`; list still shows the clone `completed` | `31d798d7-a62d-489d-82a5-32204dc4ee5e`, list `50656dcc-5fb1-429a-b953-d30c9943a0f0` |

## Run 2 (TTS `068e5679`, clone-validation `796b95a5` + manual retry `97310e66`, repro `bbd031dc`)

### Test outcomes
| Test | Result |
|---|---|
| test_pronunciation (F1) | FAIL (expected) |
| test_voices::test_documented_pro_voices_exist_with_their_language (F2) | FAIL (expected) |
| all other 14 TTS tests, incl. 5 skill-claims and the WS backoff test | pass |
| cloning test_validation[audio/x-wav] | FAIL (C2): 400 `Invalid file type.` `a91654af-4ed9-4685-b4c7-09696441dd6e` |
| cloning test_validation[audio/vnd.wave] | FAIL: transport error (A2), SSL EOF, no response; manual retry → 400 `Invalid file type.` `752e10c0-9b87-4423-aab1-7f20f6f5d615` |

### Findings
| Finding | Observed | x-request-id |
|---|---|---|
| F1 | stale id → 200 WAV 103,484 B | create `5ada8393-70c4-4a73-9617-d71575f7bd3a`, delete `575542b0-8f04-4dd9-ad6e-a5b7bafbae58`, stale `328a8ede-2aa6-4d7e-852f-254b6b16d75a` |
| F2 | same 4/208 missing | `623dd293-0e05-49ba-9c63-b03e91b87d86`, `9af9e6e2-b7f0-4921-8b0d-fd83ed5479c5` |
| F3 | ulaw 200, alaw 200, Accept same, catalogs scoped, mismatch 400 | `b9733980-bd3d-4b77-9850-5636f04cd5f8`, `0285b172-0b2d-47a9-999e-42c2b2609b01`, `7abc74b2-e697-40b6-86fc-564ead934a57`/`cdd5245c-c272-4818-95f8-e1932f5e02b9`, `4909beb0-7dd0-4d8a-a761-0fe41127d8be`, `f932d677-d9cc-47b9-a20d-b7686ff95266` |
| 3.3 WS | complete after last chunk: default 3896 ms, backoff 0 → 0.0 ms | `d28981ea-daf1-4529-8177-0cae426418c8`, `472d93dd-91a1-4827-8c6b-6aa7b30c02ac` |
| Clone create | 200 `voice_MUFo6l1O8A` (8.7 s) | `8f1d9fef-d4c1-4bb7-8aca-131aa061e49e` |
| C3 | **0/4 stray.** #1 "Is my clone voice speaking?" (no "This", A3); #2–4 clean | `ee402aa7-bff8-448f-a183-ecf54849e1a8`/`8b3111ab-6593-40ee-b17f-a9317f362c67`, `1990cefc-54f3-468f-bc46-31557c365020`/`f1adc373-48b8-4415-a939-df39921750a1`, `ebe256cf-9c97-4127-8810-a86017eec2e9`/`fafccd36-f3ee-4605-8654-b97aad890761`, `9ff05f4f-41d7-4eba-979f-857f89b0cbbb`/`314c93c8-5333-49a8-818d-0c5a94d72303` |
| C5 | 200, "This is my clone voice speaking." sim 0.98 | `b4a7f645-b242-44df-8773-3f6908527629` / STT `98e2cb75-9c7e-4c78-8ca6-539bb2088b8c` |
| C4 | **2/3 unintelligible**: #1 "커키노와 굳이 한니 현반생과 슈파십" sim 0.00; #3 "공강 굳이 한니4반します" sim 0.18; #2 sim 0.70 | `71c98c19-3e2f-424a-ab12-0d88ea695a5b`/`730e378c-bc4d-4da1-b90a-a87c4cf5277a`, `f6555724-bf02-4536-8b91-cfd513eafbc8`/`a737e8bd-7947-4bed-bcab-eed79feba23a`, good `f791e3aa-02e3-4753-9164-d435c1cd7688`/`7f9afe19-b505-4934-adf7-04c3a46fb0ab` |
| C1 | DELETE 410 `MODEL_DEPRECATED`; still listed | `08ab3d80-4ee6-4c2c-a296-a6cdd002220d`, list `a953399a-6cb3-4edb-b1a9-318e8f8074fd` |

## Run 3 (TTS `f6073382`, clone-validation `466040f8`, repro `8f506989`)

### Test outcomes
| Test | Result |
|---|---|
| test_pronunciation (F1) | FAIL (expected) |
| test_voices::test_documented_pro_voices_exist_with_their_language (F2) | FAIL (expected) |
| all other 14 TTS tests | pass |
| cloning test_validation[audio/x-wav] | FAIL (C2): 400 `Invalid file type.` `8a0c85c4-edff-4867-9eb6-2fc794690511` |
| cloning test_validation[audio/vnd.wave] | FAIL (C2): 400 `Invalid file type.` `d251e465-299f-4245-9c42-b08a5611c90b` |

### Findings
| Finding | Observed | x-request-id |
|---|---|---|
| F1 | stale id → 200 WAV 89,564 B | create `9bdd3e30-56c9-484a-a65a-6ff225a4a374`, delete `8bf8b377-83ea-428c-8554-22d518bddfb2`, stale `4823246a-f59e-40a6-90da-34a8b7371066` |
| F2 | same 4/208 missing | `d434ea54-13fc-4a28-aceb-0ecc93782215`, `27c8a06c-9242-4f50-a068-739f511b16c0` |
| F3 | ulaw 200, alaw 200, Accept same, catalogs scoped, mismatch 400 | `b4f8fa22-247f-4d6c-a106-99bb57c87dd0`, `5c669301-d649-48f5-a88b-2a5b12697fa7`, `b133ca55-5834-4f80-a31e-6f406369229f`/`4c99be75-1971-4bcb-8813-ff5c5e88ca0e`, `e8cfdbc3-f184-4173-868c-54766ddd1bd1`, `6aa0048c-0b57-4edc-a126-a4cf8502b837` |
| 3.3 WS | default 3988 ms, backoff 0 → 0.1 ms | `98603708-fc60-4cf9-8d34-7f3be0ee0ffb`, `bf6a841e-403c-44f9-9b55-08603f50b9eb` |
| Clone create | 200 `voice_MP5POBtYFB` | `e9ab06cd-b362-4fd1-b607-a3863a508e07` |
| C3 | **0/4 stray** by the script's rule; #2 "Yes, is my cloned voice speaking?" is ambiguous (A4); #1, #3, #4 clean | `eaecd80b-07b8-4183-8d7f-44a8aabe1411`/`468ef5b1-ed54-4113-b2e4-e58b4c240854`, `a722109b-73cf-4aba-9440-7b116d7c458a`/`e4b8226a-ae39-49cc-bffc-0e7e39004e86`, `8439d1c9-e99c-4677-a009-5235eae67785`/`c9a0e3a6-4bbf-405a-bb11-b06405d4ada9`, `aa63fd6a-fc45-4f14-8c91-8521bc8b36e1`/`1b91c393-c250-4f9a-81ba-c15c85786261` |
| C5 | 200, "This is my cloned voice speaking." sim 1.00 | `28d924c2-47d0-444d-a099-0160ce41cc48` / STT `e39c71d6-4e4a-4750-8d1d-a0bf03b0eb51` |
| C4 | 0/3 unintelligible (sim 0.74, 0.77, 0.78) | `42e6751c-9999-4d76-b28a-8cdb4c668aee`/`46914ad1-58c3-4b0c-bcbd-443246184f62`, `deefd8b4-6ef9-48c0-94af-0560e3bb6324`/`9f3b91d5-89bc-4708-b210-2502dec7d100`, `89b0444d-5449-4290-9cd9-c588bb864742`/`0b182c8c-f9e9-4de4-9106-d581971a4e3a` |
| C1 | DELETE 410 `MODEL_DEPRECATED`; still listed | `b9b01fb4-c7ce-4477-99f3-e2075d510a1c`, list `8a6d07bb-16f3-4dd4-a1c4-fe2f1f4592d7` |

## Clones created (the API can't delete them; delete in the dashboard)
- `voice_9EtJpn840B` (qa-repro-r1-5a488b8b)
- `voice_MUFo6l1O8A` (qa-repro-r2-bbd031dc)
- `voice_MP5POBtYFB` (qa-repro-r3-8f506989)

No clone was created by the MIME tests or the manual retries: all were rejected or dropped.

## Cost
- **TTS characters:** about 5,300.
  - pytest TTS suite: 1,518 + 1,540 + 1,540 = about 4,600, counted from logged request bodies.
  - repro script: 3 × 234 = 702.
- **Pulse STT:** 24 calls, about 65 s of audio. There were no 429s.
- **Clone creates:** 3 succeeded. 7 MIME uploads were rejected or dropped.

## Caveats
- **C3 and C4 counts** rest on Pulse STT plus a simple text rule. A3 and A4 show where that rule is ambiguous. Listening to `out/repro/run2/c3_pro_1.wav` and `out/repro/run3/c3_pro_2.wav` would settle them.
- **A1** depends on the harness's 10 s idle timeout.
- **A2** may be local network or TLS, not the API.
