> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Authentication

> Create an API key, authenticate your requests, and verify the key works. Browser and mobile clients use short-lived access tokens instead.

Every request to the Smallest AI API requires an API key in the `Authorization` header. Server-side code uses the key directly. Browser and mobile clients use a [short-lived access token](/api-reference/token-based-authentication) minted from the key.

```
Authorization: Bearer YOUR_API_KEY
```

## Create your API key

#### Open the API Keys page

Go to [API Keys](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=authentication) in the [Smallest AI console](https://app.smallest.ai/dashboard).

![Smallest AI console with API Keys section open](/_fern-files/_img/2485b6d1a1e2784842aed6627f0ff407382aeff10d4970982f2024e43680c372.webp)

#### Create a new key

Click **Create API Key** in the top-right corner, enter a name (e.g., `my-tts-app`), and click **Create API Key** to confirm.

![API Keys page showing the Create API Key button](/_fern-files/_img/9bee0666597b5f1da251ddc4d521f47d0275f4fb74dc5be1b89a0ca78b8bad3d.webp)![Create New API Key dialog with API Name field and Create API Key button](/_fern-files/_img/91874b47799b60d6ff225693ef6de002e3bdd25fc056d69a5ec6fb62a7872fde.webp)

#### Copy the key

The new key appears in your dashboard. Click the copy icon - **it's shown only once at creation**, so copy it now.

![API Keys dashboard showing the newly created key with copy icon highlighted](/_fern-files/_img/0c9cbc1ceced23a9e01808372ed3438e0a6fd6286f87128b69240dfefadf5e74.webp)

#### Set it in your environment

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

Add this to your `.bashrc` or `.zshrc` to persist across sessions.

## Try requests in the API playground

Every endpoint page in the API reference has a **Try it** button that sends a real request from your browser, using your key.

1. Create a key on the [API Keys](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=authentication) page if you don't have one yet.
2. Open an endpoint page, for example [Synthesize Speech](/api-reference/models/text-to-speech/synthesize-speech), and click **Try it**.
3. In the **Enter your credentials (Authorization)** box, paste the key into the **BearerAuth** field. Paste only the key. The playground adds `Bearer ` in front for you.
4. Click **Send request**.

The same key works for Voice Agents API and Models API endpoints. Playground requests are real API calls, so they count toward your usage like any other request.

> **Note**
>
> A `401` in the playground means the key didn't go through. `No token provided` means the **BearerAuth** field is empty. `unauthorized` (Models API) or `Unauthorized: Invalid token` (Voice Agents API) means the key is wrong, or it was pasted with `Bearer ` in front of it.

## Test your key

Confirm the key works by hitting two endpoints - one for TTS, one for STT - directly from your terminal. No install required.

### Generate speech (Lightning TTS)

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{"text": "Hello from Smallest AI.", "voice_id": "meher", "model": "lightning_v3.1_pro", "sample_rate": 24000, "output_format": "wav"}' \
  --output hello.wav
```

Play `hello.wav` - you should hear the generated audio.

### Transcribe audio (Pulse STT)

```bash
curl -X POST "https://api.smallest.ai/waves/v1/stt/?model=pulse&language=en" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/smallest-inc/cookbook/raw/main/speech-to-text/getting-started/samples/audio.wav"}'
```

You'll get back:

```json
{
  "status": "success",
  "transcription": "This is a sample audio file for testing speech-to-text transcription with the pulse api.",
  "words": [],
  "utterances": [],
  "metadata": { "duration": 5.6, "fileSize": 268844 }
}
```

## Use your key in code

Include the `Authorization: Bearer YOUR_API_KEY` header on every request.

**`cURL`**

```bash cURL
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{"text": "Authentication test", "voice_id": "meher", "model": "lightning_v3.1_pro", "output_format": "wav"}' \
  --output test.wav
```

**`Python`**

```python Python
import os
import requests

response = requests.post(
    "https://api.smallest.ai/waves/v1/tts",
    headers={
        "Authorization": f"Bearer {os.environ['SMALLEST_API_KEY']}",
        "Content-Type": "application/json",
        "Accept": "audio/wav",
    },
    json={"text": "Authentication test", "voice_id": "meher", "model": "lightning_v3.1_pro", "output_format": "wav"},
)
```

**`JavaScript`**

```javascript JavaScript
const response = await fetch(
  "https://api.smallest.ai/waves/v1/tts",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
      "Content-Type": "application/json",
      Accept: "audio/wav",
    },
    body: JSON.stringify({
      text: "Authentication test",
      voice_id: "meher",
      model: "lightning_v3.1_pro",
      output_format: "wav",
    }),
  }
);
```

## Browser and mobile clients

Never ship the API key to a browser or mobile app. Mint a short-lived access token on your server and let the client authenticate TTS, STT and speech-to-speech calls with it. See [Token-Based Authentication](/api-reference/token-based-authentication).

## Content expiry (Enterprise)

Enterprise plans can add one more header to any TTS, STT or LLM request so that its content is not retained:

```
x-expire-content: true
```

That request's content is expired within 7 days and the usage record is kept. Organizations can also have zero retention or a retention window set on every request, with no header. On other plans the header is ignored and the request is processed normally. See [Zero Data Retention](/models/enterprise/zero-data-retention).

## Security

> **Warning**
>
> Your API key is a secret. Never expose it in client-side code, public repositories, or browser applications. For browser and mobile clients, mint a [short-lived access token](/api-reference/token-based-authentication) on your server, or proxy the call through your backend.

* Store keys in environment variables, not in source code
* Use `.env` files locally and add `.env` to `.gitignore`
* Rotate keys periodically from the [API Keys page](https://app.smallest.ai/dashboard/api-keys)
* Each key tracks usage against your account quota - see [Concurrency and Limits](/api-reference/concurrency-and-limits)

## Error responses

| Status                  | Meaning                                                                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `401 Unauthorized`      | Missing or invalid API key, or an expired access token                                                                                                    |
| `403 Forbidden`         | Key doesn't have access to this resource, an access token was used on a route outside its allowed list, or an access token was used to mint another token |
| `429 Too Many Requests` | Rate limit exceeded - wait and retry                                                                                                                      |

For rate limits and concurrency, see [Concurrency and Limits](/api-reference/concurrency-and-limits).