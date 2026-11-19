> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Text to Speech API Quickstart: First Audio in 60 Seconds

> Generate your first speech audio in under 60 seconds with the Lightning text to speech API: get an API key, make the first request, play the result.

## Step 1: Get Your API Key

Open the [API Keys page](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=text-to-speech-quickstart) in the [Smallest AI console](https://app.smallest.ai/dashboard).

![Smallest AI dashboard with API Keys highlighted under Developer section in the left sidebar](/_fern-files/_img/2485b6d1a1e2784842aed6627f0ff407382aeff10d4970982f2024e43680c372.webp)

Click **Create API Key** in the top-right corner, enter a name, and click **Create API Key** to confirm.

![API Keys page showing the Create API Key button](/_fern-files/_img/9bee0666597b5f1da251ddc4d521f47d0275f4fb74dc5be1b89a0ca78b8bad3d.webp)![Create New API Key dialog with API Name field and Create API Key button](/_fern-files/_img/91874b47799b60d6ff225693ef6de002e3bdd25fc056d69a5ec6fb62a7872fde.webp)

The new key appears in your dashboard. Click the copy icon to copy it.

![API Keys dashboard showing the newly created key with copy icon highlighted](/_fern-files/_img/0c9cbc1ceced23a9e01808372ed3438e0a6fd6286f87128b69240dfefadf5e74.webp)

Export the key in your terminal:

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

> **Tip**
>
> New to Smallest AI? [Sign up here](https://app.smallest.ai?utm_source=documentation\&utm_medium=text-to-speech) first.

## Step 2: Hear Audio in 30 Seconds

Paste this in your terminal - no install required:

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{"text": "Hello from Smallest AI. This is Lightning v3.1 Pro.", "voice_id": "meher", "model": "lightning_v3.1_pro", "sample_rate": 24000, "output_format": "wav"}' \
  --output hello.wav
```

Play `hello.wav` - it should sound like this:

That's broadcast-quality TTS with \~200ms TTFB.

> **Tip**
>
> The `model` field selects which Lightning pool serves the request - `lightning_v3.1_pro` is the new premium pool with a curated voice catalog, and `lightning_v3.1_pro_10_26` is a [preview Pro checkpoint](/model-cards/text-to-speech/lightning-v-3-1-pro#checkpoints) for English, Spanish and Hindi (`en`, `es`, `hi`).

## Step 3: Build It Into Your App

**`cURL`**

```bash cURL
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{
    "text": "Modern problems require modern solutions.",
    "voice_id": "meher",
    "model": "lightning_v3.1_pro",
    "sample_rate": 24000,
    "speed": 1.0,
    "language": "en",
    "output_format": "wav"
  }' --output output.wav
```

**`Python`**

```python Python
import os
import requests

API_KEY = os.environ["SMALLEST_API_KEY"]

response = requests.post(
    "https://api.smallest.ai/waves/v1/tts",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "audio/wav",
    },
    json={
        "text": "Modern problems require modern solutions.",
        "voice_id": "meher",
        "model": "lightning_v3.1_pro",
        "sample_rate": 24000,
        "speed": 1.0,
        "language": "en",
        "output_format": "wav",
    },
)

with open("output.wav", "wb") as f:
    f.write(response.content)
print(f"Saved output.wav ({len(response.content):,} bytes)")
```

**`Python SDK`**

```python Python SDK
# Requires: pip install smallestai
from smallestai import SmallestAI

client = SmallestAI()  # reads SMALLEST_API_KEY from the environment

audio_chunks = client.waves.synthesize_tts(
    text="Modern problems require modern solutions.",
    voice_id="meher",
    model="lightning_v3.1_pro",
    sample_rate=24000,
    speed=1.0,
    output_format="wav",
)

with open("output.wav", "wb") as f:
    f.write(b"".join(audio_chunks))
print("Saved output.wav")
```

**`JavaScript`**

```javascript JavaScript
const fs = require("fs");

const API_KEY = process.env.SMALLEST_API_KEY;

const response = await fetch(
  "https://api.smallest.ai/waves/v1/tts",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
      Accept: "audio/wav",
    },
    body: JSON.stringify({
      text: "Modern problems require modern solutions.",
      voice_id: "meher",
      model: "lightning_v3.1_pro",
      sample_rate: 24000,
      speed: 1.0,
      language: "en",
      output_format: "wav",
    }),
  }
);

const buffer = Buffer.from(await response.arrayBuffer());
fs.writeFileSync("output.wav", buffer);
console.log(`Saved output.wav (${buffer.length} bytes)`);
```

> **Note**
>
> The `smallestai` Python SDK example uses `client.waves.synthesize_tts`, which returns audio byte chunks you can join and save. `synthesize_sse_tts` streams the same request over SSE.

> **Note**
>
> For browser or mobile clients, keep the API key on your server and mint a [short-lived access token](/api-reference/token-based-authentication) for the client.

> **Tip**
>
> **Full runnable source files:** [Python](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-python.py) | [JavaScript](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-javascript.js) | [cURL](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-curl.sh)

## Step 4: Explore More

#### [Lightning v3.1 Pro](/model-cards/text-to-speech/lightning-v-3-1-pro)

Premium voice catalog across American, British, and Indian accents, plus dedicated voices for 29 additional languages (adds Dutch, Swedish over v3.1). Pass `model: lightning_v3.1_pro` to use.

#### [Voices & Languages](/models/text-to-speech/voices-languages)

Browse 217 voices across 12 languages on the standard pool - English, Hindi, Spanish, and 9 Indian languages.

#### [Streaming TTS](/models/text-to-speech/streaming)

Real-time audio streaming via WebSocket for voice assistants.

#### [Voice Cloning](/models/voice-cloning/instant-clone-ui)

Clone any voice from just 5-15 seconds of audio (standard pool only).

## Key Parameters

| Parameter       | Type   | Default          | Description                                                                                                                            |
| --------------- | ------ | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `text`          | string | *required*       | Text to synthesize (max \~250 chars recommended)                                                                                       |
| `voice_id`      | string | *required*       | Voice to use (e.g., `meher`, `blake`)                                                                                                  |
| `model`         | string | `lightning_v3.1` | TTS pool: `lightning_v3.1` (standard), `lightning_v3.1_pro` or `lightning_v3.1_pro_10_26` (preview; `en`, `es`, `hi`)                  |
| `sample_rate`   | int    | `44100`          | `8000`, `16000`, `24000`, or `44100` Hz                                                                                                |
| `speed`         | float  | `1.0`            | Speech rate: `0.5` to `2.0`                                                                                                            |
| `language`      | string | `en`             | Language code matching the voice - `en`, `hi`, `es`, `ta`, etc. See `tags.language` via `GET /waves/v1/lightning-v3.1-pro/get_voices`. |
| `output_format` | string | `pcm`            | `pcm`, `wav`, `mp3`, `ulaw`, or `alaw`                                                                                                 |

## Need Help?