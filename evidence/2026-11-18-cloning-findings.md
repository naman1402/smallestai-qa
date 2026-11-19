# Voice cloning findings, 2026-11-18 (confirmed live)

- **Run:** 2026-11-18, 17:00–17:45 IST, against `https://api.smallest.ai`.
- **Raw evidence:** `evidence/2026-11-18.jsonl`. Search for the `x-request-id`.
- **Docs compared against:** `docs/reference/smallest-docs-2026-11-18/models__voice-cloning__instant-clone-api.md`. Re-checked against the live page at 17:20 IST: the delete section is unchanged.
- **Sample:** the owner's own voice. A 12 s mono 24 kHz WAV cut from `samples/my_voice.wav`, which is git-ignored.

| ID | Finding | Severity | Status |
|---|---|---|---|
| C1 | Clones can't be deleted through the API: the only documented delete route returns 410 `MODEL_DEPRECATED` | High | **Permanent: 4/4 runs** |
| C2 | Clone upload rejects valid WAV files based on the declared MIME type | Medium | **Permanent: 4/4 runs** |
| C3 | Pro clones add a stray sound at the start of the audio when the sample starts with silence | Observation | **Intermittent:** 2 of 4 clones affected (it depends on the clone) |
| C5 | The documented "clone must match its pool" rule is not enforced; clones work on both models | Medium | **Permanent: 4/4 runs** |
| C4 | Cross-lingual Pro clone sometimes returns unintelligible audio (Japanese: 2 of 9) with a 200 | Observation | **Intermittent:** 4 of 18 clips across 2 sessions |

Reproduce C3 and C5: `.venv/bin/python scripts/explore_clone_languages.py` (creates 2 clones; listen to `out/clone-xlang/`) and `.venv/bin/pytest tests/cloning -v`.
Audio was checked with Smallest's Pulse STT: each clip is transcribed and scored 0–1 against the input text. The same text spoken by a native catalog voice is the baseline, so a low clone score means the clone lost the content, not the STT.

---

## C1: The only documented way to delete a voice clone returns 410 `MODEL_DEPRECATED`

**What happens.** The cloning doc's "Delete a clone" section says:

> "The current public delete endpoint lives at `/waves/v1/lightning-large` despite the path suggesting otherwise - it deletes any voice clone on your organization regardless of the underlying model."

Sent exactly as the doc's curl, against a clone created seconds earlier, it returns:

```
HTTP/2 410
{"status":"error","error_code":"MODEL_DEPRECATED",
 "message":"This model is retired. Please migrate to lightning-v3.1 via /api/v1/lightning-v3.1/get_speech.",
 "recommended_endpoint":"/api/v1/lightning-v3.1/get_speech"}
```

The clone is still listed as `completed` afterwards. The delete route sits under the `lightning-large` path and was retired with that model.

**What we ruled out (is it us?)**
- **Request shape:** we sent the doc's curl verbatim (method, path, `Content-Type: application/json`, body `{"voiceId": "<id>"}`). The same 410 came back from both our harness and plain curl.
- **Stale docs snapshot:** the live doc page still documents only this route.
- **API reference:** it has pages for create and list clones but no delete page. `llms.txt` lists no clone-delete endpoint.
- **SDK:** `smallestai` 5.14.0, the latest on PyPI, has `create` and list clone methods but no clone delete.
- **Smallest's agent skills:** no mention of deleting clones.
- **Dashboard:** the owner deleted `voice_s7UVkBADFy` from the dashboard without trouble. So deletion exists in the product; only the API has no working, documented route.

**Why a customer cares.**
- A voice clone is biometric voice data. Customers with end-user consent flows, GDPR/DPDP erasure requests or retention policies need to delete clones programmatically, for example when a user closes their account.
- Today that needs a person clicking in the dashboard for each clone.
- The error message makes it worse. It tells you to "migrate" to `/api/v1/lightning-v3.1/get_speech`, which is a speech-generation endpoint (not a delete), on a model that itself retires 2026-11-30.

**Evidence**
| Step | Result | x-request-id |
|---|---|---|
| Create clone `voice_slCdbOl2b2` (`audio/wav`, Pro pool) | 200, `completed` | `8b99063b-a341-4746-b518-1847eead6305` |
| Create clone `voice_s7UVkBADFy` (`audio/wave`, Pro pool) | 200, `completed` | `bf11222d-d6fe-44bb-9b6f-8bb5cb241664` |
| `DELETE /waves/v1/lightning-large {"voiceId": "voice_slCdbOl2b2"}` | **410 `MODEL_DEPRECATED`** | `e33b55f1-d11a-4ede-ad7e-5164b1831f54` |
| `DELETE /waves/v1/lightning-large {"voiceId": "voice_s7UVkBADFy"}` | **410 `MODEL_DEPRECATED`** | `464b6f67-a21e-4365-8731-4092f8d8689e` |
| List clones after both deletes | both still listed, `completed` | `f53b07d9-3d7f-4a3b-918f-954eceaa3b75` |
| Owner deletes `voice_s7UVkBADFy` in the dashboard, then list | only `voice_slCdbOl2b2` left | `0e268536-7d2c-438d-822d-f52c3acd930f` |
| Re-check with the doc's exact curl (`voice_slCdbOl2b2`) | **410 `MODEL_DEPRECATED`** | `23be11a1-a127-465c-a49c-c545dd1fa2ce` (plain curl, outside the harness, so not in the raw log) |

**Expected:** a working, documented delete in the API reference and SDK, for example `DELETE /waves/v1/voice-cloning/{voiceId}`. Retiring a model should not take clone management down with it.

**Reproduce**
```bash
# 1. create a clone from your own 5-15 s WAV (note the explicit audio/wav type, see C2)
curl -s https://api.smallest.ai/waves/v1/voice-cloning -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -F displayName=qa-delete-check -F model=lightning-v3.1-pro -F language=en -F "file=@my_voice.wav;type=audio/wav"
# 2. delete it exactly as documented
curl -s -i -X DELETE https://api.smallest.ai/waves/v1/lightning-large -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" -d '{"voiceId":"<voiceId from step 1>"}'
# -> HTTP 410 MODEL_DEPRECATED; GET /waves/v1/voice-cloning still lists the clone
```
Clean up by hand afterwards in the dashboard (Voice Cloning).

---

## C2: Clone upload rejects valid WAV files based on the declared MIME type

**What happens.** We sent the same 12 s WAV bytes to `POST /waves/v1/voice-cloning` five times, changing only the file part's `Content-Type`:

| Declared type | Result | x-request-id |
|---|---|---|
| `audio/wav` | 200, clone created | `8b99063b-a341-4746-b518-1847eead6305` |
| `audio/wave` | 200, clone created | `bf11222d-d6fe-44bb-9b6f-8bb5cb241664` |
| `audio/x-wav` | **400 `Invalid file type.`** | `6ed50388-bb38-4474-9dc6-5746f2928a37` |
| `audio/vnd.wave` (the IANA-registered WAV type) | **400 `Invalid file type.`** | `37b1d9b0-04ca-45d6-9927-ebd0f8b5527b` |
| `application/octet-stream` | **400 `Invalid file type.`** | `c3b29f1a-fc81-42a9-a02e-ba2f88875ec1` |

The server decides by the declared label, not the file's contents. The docs say only "Supported types: .mp3, .wav, .mp4, .webm" and list no accepted MIME types.

**Why a customer cares.**
- `audio/x-wav` is a very common label for `.wav`.
- Python's standard `mimetypes` assigns `audio/x-wav` on older versions and `audio/vnd.wave` on 3.14.
- Generic uploaders send `application/octet-stream`.
- Any of these gets "Invalid file type." for a valid WAV, and the message doesn't say which type was expected. This is how our own first run failed (`c3cfa9a3-ecb0-4356-807f-1b83f514bd9b`, `03bd15ac-439b-41f6-90c2-17fd2e0c4c0e`).

**Expected:** detect the format from the file bytes (WAV files start with `RIFF....WAVE`), or at least accept the common WAV aliases. Failing that, document the accepted MIME types and name them in the error.

**Reproduce:** run the curl from C1 step 1 with `type=audio/x-wav` → 400 `Invalid file type.`. With `type=audio/wav` → 200. Delete the clone in the dashboard afterwards.

---

## C3: Pro clones add a stray sound at the start when the sample starts with silence

> **Re-run result:** 3 more Pro clones from the same recording. Run 1's clone had the stray sound in 4 of 5 clips; the run 2 and run 3 clones had 0 of 5 each. So 2 of 4 clones are affected: it varies per clone, not per request. Kept as an observation, because it doesn't reproduce every run. See `2026-11-18-reproducibility.md`.

**What happens.** The owner's 12 s sample has 1.5 s of silence or breath before the first word (Pulse puts the first word "This" at 1.52 s; `4c21fd25-8c02-47f7-ab4e-6a5ed21d3f06`). A Pro clone made from it often starts its output with a sound that isn't in the text. The STT hears it as a short word: "Hello", "To", "Do", "Two", "Just like", "तो", "டு", "Fue".

| Clone (same recording) | Clips with a stray opening sound | Examples |
|---|---|---|
| Pro, sample as recorded | **4 of 8** in a controlled re-run; about 10 of 25 across the session | "To this is my clone voice speaking." `bdfce9a3-eef8-4a51-975c-ba606ecfe6b5`; "Just like this is my…" `5630c6da-603f-4677-8e2a-89024634b91f`; "Two हवाई अड्डे…" `d4117540-dce0-4b1e-b3b8-482b9fec1678`; "Hello, this is my cloned voice speaking." `44d9699a-f764-4c0b-8008-1c7867269734`; "Do the train…" `41664841-9998-4132-9264-a56e551a87cf` |
| Pro, same recording with leading silence trimmed (`voice_tTSsaeuTUM`) | **0 of 8** | `cca9c4c1-6508-4f1d-b191-36c50c10b56e`, `b716d7ce-80a1-45ca-9d11-b4f158cafb51`, `602aad3a-6dc2-48fb-8522-c49e606554dc`, `8c140e97-bbdf-47be-979e-14dacd20b548` |
| Standard (v3.1), sample as recorded | 0 of 5 | `20c1ddb3-ce87-4513-b244-79bcd03f5953`, `f555e973-b0a6-4d16-b8f7-1cb257375af1`, `d717daca-efcb-4a9b-ad3c-5c4691654848` |
| Catalog voices, same texts | 0 of 13 | for example `f37baa81-d6b9-4ebb-b750-93a8b6d6ca11` |

**Why a customer cares.**
- Almost every real recording starts with some silence: phone and browser recorders, consent flows. The docs' recording guidance doesn't say to trim it, and the API doesn't trim it either.
- The result is a Pro clone that says a random syllable before roughly half of its sentences.
- In a voice agent, every turn can start with "uh / to / two". It's audible, and there's no error to catch.

**Expected:** trim leading and trailing silence on upload, or reject or warn about samples with long silence, or at least document it.

**Listen:** `out/clone-xlang/artifact_pro-orig_lifecycle_1.wav` vs `artifact_pro-trimmed_lifecycle_1.wav`. Owner listening check (2026-11-18): the untrimmed clip audibly starts with "two"; the trimmed one does not.

---

## C5: The documented "clone must match its pool" rule is not enforced

**Docs:** pair a clone with the TTS model matching its `modelIds`; "a mismatched pair returns 400". The docs also warn of ~100–200 byte "empty" WAVs.

**Live:** both directions return 200 with full, correct speech (STT similarity 0.9–1.0):

| Clone (`modelIds`) | TTS model | Result | x-request-id |
|---|---|---|---|
| `['lightning-v3.1']` | `lightning_v3.1_pro` | 200, "This is my cloned voice speaking." | `bc458d27-2880-494c-b6df-a4e177be8132` (also `1cabd851-1bc6-4f52-8bd7-128b4513358e`) |
| `['lightning-v3.1-pro']` | `lightning_v3.1` | 200, "Hello, this is my clone voice speaking." (C3 opening) | `9c0e56c5-831a-4929-afff-7e8b9afa9bfd` (also `37d70e3e-cc3e-4c65-92a4-132f4fe9b85b`) |

Catalog voices, by contrast, are rejected: `magnus` on Pro gets 400 (`69d9e14d-4ea2-4f3a-aedf-c03abe897391`).

**Why a customer cares.**
- The docs push customers to check `modelIds` and recreate clones for the right pool, which may be unnecessary work.
- More importantly, the Nov 30 warning ("clones made on lightning-v3.1 will stop working") is unclear: a v3.1 clone already speaks on Pro today.
- Customers can't tell from the API which pool and which voice actually served the request.

**Owner listening check (2026-11-18):** the v3.1 clone on the Pro model (`defaultclone_on_lightning_v3.1_pro.wav`) sounds right, so it is not a fallback voice. The same clone on its *matching* model (`defaultclone_on_lightning_v3.1.wav`, `921a9929-0a08-45a1-ac3b-064e994ece9a`) has an audible gap mid-sentence: silence detection measures a 0.26 s pause at 0.57–0.83 s ("This is … my cloned voice"). That's one sample, so it's an observation, not a finding.

---

## C4 (observation): Cross-lingual Pro clone sometimes returns unintelligible audio, with a 200

**Docs:** "Cross-lingual cloning is supported (e.g., English reference used for Spanish output)."

**Live:** an English-recorded Pro clone spoke Japanese 9 times with the same request.
- **2 of 9 were unintelligible.** Told to expect Japanese, Pulse STT returned Korean text: "고소와 굳이 한니 현반생과로 싶" and "군고위기노와 굳이 한 이 연반생과를 주파십". Similarity to the input: 0.0.
- **The other 7 scored 0.67–0.81.** The native catalog voice `aria` scored 0.67–0.84 over 4 runs and never failed.
- Every response was 200.

| Clip | x-request-id |
|---|---|
| Bad | `54a31f30-edf6-4bfa-9d61-410b6eec4f9b` (STT `5d277a47-44ba-4a7d-bca3-96b2967dfea7`), `2c063b95-a29a-4f08-a4a8-468dd2e52f9b` |
| Good | `e291fb99-60f9-44e4-a85e-c3b8a8d5b923`, `46b7ab51-d47c-4bfe-8ad2-ce36ddfa3365`, `706dfcca-f903-486e-a201-2f8685d21938` |
| Native `aria` | `4f0d0814-47fe-4aa9-9120-9f0d716e272d`, `95342de6-8ac6-4abb-9243-778816a133e1` |

**Why it is only an observation:**
- 9 runs is a small sample, from one language and one speaker.
- The scoring uses Smallest's own STT. The native-voice baseline controls for that, but it is still a dependency.
- The pattern matters anyway. The same request sometimes yields wrong-language gibberish with no signal, so a customer could only catch it by transcribing every clip.

**Listen:** `out/clone-xlang/clone-pro_ja.wav` and `clone-pro_ja_r4.wav` (bad) vs `clone-pro_ja_r5.wav` (good).

**Reproduce:** `scripts/explore_clone_languages.py` covers the first run. For repeats, send the same Japanese request 5–10 times and transcribe each clip with `POST /waves/v1/stt/?model=pulse&language=ja`.

---

## Worked as documented
- Lifecycle on both pools: create → listed with the right `modelIds` → speaks on REST, SSE and WebSocket.
- Cross-lingual output in Spanish, French, German, Hindi, Tamil, Chinese and Hinglish from the English-recorded clone was intelligible, matching the docs' claim. Japanese was the exception (C4).

## Leftover clones (the API can't delete them, C1). Delete in the dashboard:
- `voice_Qpz2jeHsNO` (qa-default-94fc7b11)
- `voice_ryXy8rVYD4` (qa-pro-94fc7b11)
- `voice_qgaVYdrk99` (qa-shorter_than_5s-94fc7b11)
- `voice_VWYjCbGEM0` (qa-xlang-pro-f0a4469e)
- `voice_FYER5AvK1q` (qa-xlang-standard-f0a4469e)
- `voice_tTSsaeuTUM` (qa-trimmed-pro-d4000e06)

As of `68a1101b-036f-4565-8c41-f05bd97637b7`.
