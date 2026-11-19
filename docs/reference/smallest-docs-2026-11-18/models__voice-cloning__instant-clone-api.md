> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Voice Cloning API: Clone a Voice in One HTTP Call

> Create an instant voice clone from a 5 to 15 second audio sample with one POST request, then use the cloned voice in Lightning text to speech.

Create an instant voice clone via a single `POST` call. Uploads the audio, runs preprocessing, and returns pre-generated sample clips of the cloned voice - all in one request.

> **Tip**
>
> This is the recommended way to clone voices programmatically. It replaces the older two-step flow and the model-specific `/lightning-large/add_voice` endpoint, which are both now deprecated.

> **Warning**
>
> Voice clones made on `lightning-v3.1` will stop working on Nov 30, 2026 (18:30 UTC). Create them again with `model=lightning-v3.1-pro`. See [Deprecation notices](/api-reference/deprecations/models).

## Requirements

* A Smallest AI API key - grab one from the [API Keys page](https://app.smallest.ai/dashboard/api-keys).
* A clean audio sample, 5–15 seconds, under 5 MB. Supported types: `.mp3`, `.wav`, `.mp4`, `.webm`.

```bash
export SMALLEST_API_KEY=sk_your_key_here
```

## Create the clone

**`cURL`**

```bash title="cURL"
curl -X POST "https://api.smallest.ai/waves/v1/voice-cloning" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -F "displayName=my-custom-voice" \
  -F "file=@/path/to/sample.wav" \
  -F "model=lightning-v3.1-pro" \
  -F "language=en" \
  -F "accent=general" \
  -F "tags=english,friendly"
```

**`Python (requests)`**

```python title="Python (requests)"
import os
import requests

with open("sample.wav", "rb") as f:
    response = requests.post(
        "https://api.smallest.ai/waves/v1/voice-cloning",
        headers={"Authorization": f"Bearer {os.environ['SMALLEST_API_KEY']}"},
        data={
            "displayName": "my-custom-voice",
            "model": "lightning-v3.1-pro",
            "language": "en",
            "accent": "general",
            "tags": "english,friendly",
        },
        files={"file": f},
    )

response.raise_for_status()
clone = response.json()["data"]
print("voice_id:", clone["voiceId"])
print("sample clips:", [s["audioUrl"] for s in clone["samples"]])
```

**`Node.js (fetch + FormData)`**

```javascript title="Node.js (fetch + FormData)"
import fs from "node:fs";

const form = new FormData();
form.append("displayName", "my-custom-voice");
form.append("language", "en");
form.append("accent", "general");
form.append("tags", "english,friendly");
form.append("file", new Blob([fs.readFileSync("sample.wav")]), "sample.wav");

const res = await fetch("https://api.smallest.ai/waves/v1/voice-cloning", {
  method: "POST",
  headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
  body: form,
});

const { data } = await res.json();
console.log("voice_id:", data.voiceId);
```

## Request fields

| Field         | Required | Description                                                                                                                         |
| ------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `displayName` | Yes      | Human-readable name for the clone. 1–500 characters.                                                                                |
| `file`        | Yes      | Audio file. Max 5 MB.                                                                                                               |
| `model`       | No       | `lightning-v3.1` (default) or `lightning-v3.1-pro` to clone onto the Pro pool. `lightning-v2` is rejected with a deprecation error. |
| `language`    | No       | Target language code. Must be one supported by the pool in `model` (e.g. `en`, `hi`).                                               |
| `description` | No       | Longer note about the clone.                                                                                                        |
| `accent`      | No       | Accent label (e.g. `general`, `indian`).                                                                                            |
| `tags`        | No       | Comma-separated list. The server splits on commas and trims whitespace.                                                             |

## Response shape

```json
{
  "message": "Voice clone created successfully",
  "data": {
    "voiceId": "voice_dLP5T67Qw7",
    "displayName": "my-custom-voice",
    "status": "completed",
    "language": "en",
    "model": { "_id": "...", "modelName": "lightning-v3.1-pro" },
    "audioFileNames": ["sample.wav"],
    "createdAt": "2026-04-20T09:42:17.103Z",
    "organizationId": "69561896a37fd214b9a8d33c",
    "samples": [
      {
        "text": "Hello! This is a sample of what I sound like.",
        "audioUrl": "https://..."
      }
    ]
  }
}
```

Use `data.voiceId` directly in any TTS call:

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is my cloned voice.",
    "voice_id": "voice_dLP5T67Qw7",
    "model": "lightning_v3.1_pro"
  }' \
  -o output.wav
```

## List your clones

```bash
curl -H "Authorization: Bearer $SMALLEST_API_KEY" \
  "https://api.smallest.ai/waves/v1/voice-cloning"
```

Returns every clone on your organization along with `modelIds` (compatible models), `status`, `language`, and creation time.

## Check model compatibility before using a clone

The `modelIds` array in the list response tells you which TTS models a clone works with. Check it before passing `voice_id` to a TTS call:

```bash
curl -H "Authorization: Bearer $SMALLEST_API_KEY" \
  "https://api.smallest.ai/waves/v1/voice-cloning" \
  | jq '.data[] | {displayName, voiceId, modelIds}'
```

```json
{ "displayName": "my-voice",   "voiceId": "voice_abc", "modelIds": ["lightning-v3.1-pro"] }
{ "displayName": "old-voice",  "voiceId": "voice_xyz", "modelIds": ["lightning-large"] }
```

| `modelIds` contains    | Works with                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| `lightning-v3.1-pro`   | `POST /waves/v1/tts` with `model: lightning_v3.1_pro`, and the unified TTS streaming and WebSocket endpoints |
| `lightning-v3.1`       | `POST /waves/v1/tts` with `model: lightning_v3.1`                                                            |
| `lightning-large` only | Deprecated `lightning-large` endpoints only - will return an empty audio response on the current pools       |

Clones created via the current `POST /waves/v1/voice-cloning` endpoint produce voices for the pool you pass in `model`. Pair the resulting `voice_id` with the matching TTS `model`; check `modelIds` on the clone if unsure. The older `POST /waves/v1/lightning-large/add_voice` endpoint (deprecated) only produces `lightning-large`-compatible voices, which will not work with the current pools.

> **Note**
>
> If you see a short (\~100–200 byte) WAV response from a TTS request with a cloned voice, the most common cause is using a `lightning-large`-only clone on a current model. Check `modelIds` on the clone.

## Delete a clone

The current public delete endpoint lives at `/waves/v1/lightning-large` despite the path suggesting otherwise - it deletes any voice clone on your organization regardless of the underlying model.

```bash
curl -X DELETE "https://api.smallest.ai/waves/v1/lightning-large" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "voiceId": "voice_dLP5T67Qw7" }'
```

## Errors

| Status                                                                        | Cause                                                                      |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 400 `No file provided`                                                        | The `file` form field is missing.                                          |
| 400 `clone limit exceeded, consider upgrading`                                | You've hit your org's instant voice-clone limit.                           |
| 400 `Invalid language. Supported: ...`                                        | `language` is not supported by the pool in `model`.                        |
| 400 `Voice cloning for lightning-v2 is deprecated. Please use lightning-v3.1` | `model=lightning-v2` was passed.                                           |
| 401                                                                           | API key missing or invalid.                                                |
| 500 with `error_code=voice_clone_timeout`                                     | Preprocessing or sample generation exceeded the timeout. Retry.            |
| 500 with `error_code=voice_clone_error`                                       | Model returned an error while processing the sample. Try a cleaner sample. |

## Migrating from the legacy endpoint

If you're currently using `POST /waves/v1/lightning-large/add_voice`, switch to `POST /waves/v1/voice-cloning`:

* **Same auth** - `Authorization: Bearer $SMALLEST_API_KEY`.
* **Same multipart shape** for `displayName` + `file`.
* **New optional fields** - `language`, `description`, `accent`, `tags`.
* **Response includes `samples`** - pre-generated audio clips of the cloned voice, which the legacy endpoint did not provide.
* **Pass `model=lightning-v3.1-pro`.** Voices cloned via the legacy endpoint only worked on `lightning-large` and returned empty audio on the current pools.

The legacy endpoint still works but is marked deprecated in the API reference.

---

Need help? Email [support@smallest.ai](mailto:support@smallest.ai) or ask on [Discord](https://discord.gg/9WtSXv26WE).

## FAQ: voice cloning API

**How much audio do I need to clone a voice?**
A clean 5 to 15 second sample under 5 MB, as `.mp3`, `.wav`, `.mp4`, or `.webm`. Recording quality matters more than length; see [recording guidelines](/models/voice-cloning/best-practices).

**How do I use the cloned voice in text to speech?**
Pass the returned `voiceId` as `voice_id` in any TTS call, with the TTS `model` that matches the pool you cloned onto. The [example above](#create-the-clone) shows the full round trip.

**Can I clone onto the premium voice pool?**
Yes. Pass `model=lightning-v3.1-pro` when creating the clone, then use the voice with the `lightning_v3.1_pro` TTS model.

**Why does my cloned voice return a tiny or empty audio file?**
Almost always a `lightning-large`-only clone used on the current pool. Check the clone's `modelIds` in the [list response](#list-your-clones) and recreate it on `lightning-v3.1-pro` if needed.