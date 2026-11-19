> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Get Started with the Speech APIs: Auth, Base URL, SDKs

> Start calling the Smallest AI speech APIs: authentication, base URL, which endpoint serves each model, the official SDKs, and where each quickstart lives.

## Before you start

#### Create an API key

Create a key on the [API Keys](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=models-overview) page and export it:

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

The same key works for every model and for the Voice Agents API. See [Authentication](/api-reference/authentication) for rotation and security guidance.

#### Send one request

Text to speech is the fastest way to confirm the key works. No install required:

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{"text": "Hello from Smallest AI.", "voice_id": "meher", "model": "lightning_v3.1_pro", "sample_rate": 24000, "output_format": "wav"}' \
  --output hello.wav
```

Play `hello.wav`. If you hear speech, you are set up.

#### Pick a capability

Each capability below has its own quickstart with Python, JavaScript, and cURL samples.

## Endpoints at a glance

Every endpoint lives under `https://api.smallest.ai/waves/v1` and authenticates with `Authorization: Bearer <key>`.

| Capability                    | Model              | Endpoint                                                                | How to select                                                                                           |
| ----------------------------- | ------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Text to speech (sync)         | Lightning v3.1 Pro | `POST /waves/v1/tts`                                                    | `"model": "lightning_v3.1_pro"` or `"lightning_v3.1_pro_10_26"` (preview; `en`, `es`, `hi`) in the body |
| Text to speech (streaming)    | Lightning v3.1 Pro | `POST /waves/v1/tts/live` (SSE) or `WSS /waves/v1/tts/live` (WebSocket) | Same `model` body field                                                                                 |
| Speech to text (pre-recorded) | Pulse, Pulse Pro   | `POST /waves/v1/stt/`                                                   | `?model=pulse` or `?model=pulse-pro`                                                                    |
| Speech to text (realtime)     | Pulse              | `WSS /waves/v1/stt/live`                                                | `?model=pulse`                                                                                          |
| Speech to speech              | Hydra              | `WSS /waves/v1/s2s`                                                     | `?model=hydra`                                                                                          |
| LLM                           | Electron           | `POST /waves/v1/chat/completions`                                       | `"model": "electron"` in the body                                                                       |
| Voice cloning                 | Lightning v3.1     | `POST /waves/v1/voice-cloning`                                          | Upload a sample, get a `voice_id`                                                                       |

Read [Choosing a transport](/models/text-to-speech/choosing-a-transport) to choose a transport, and [Compare models](/model-cards/compare) to pick one.

## Quickstarts

#### [Text to Speech](/models/text-to-speech/quickstart)

Synthesize speech in 30 seconds, then stream it.

#### [Speech to Text](/models/speech-to-text/quickstart)

Transcribe a file, then a live microphone stream.

#### [Speech to Speech](/models/speech-to-speech/quickstart)

Open a Hydra session and hold a conversation.

#### [LLM](/models/llm/quickstart)

Chat completions with the OpenAI SDK pointed at Electron.

#### [Voice Cloning](/models/voice-cloning/instant-clone-api)

Create a clone in one HTTP call and use it in text to speech.

#### [Voice agent from parts](/models/cookbooks/voice-agent-electron-pulse-lightning)

Wire Pulse, Electron, and Lightning into your own agent loop.

## SDKs

#### [Python](https://github.com/smallest-inc/smallest-python-sdk)

`pip install smallestai`. Typed clients for every endpoint, including the WebSocket streams.

#### [Node.js](https://github.com/smallest-inc/smallest-node-sdk)

The official Node.js client for the Smallest AI API.

Using an agent framework? [LiveKit](/integrations/agent-framework/live-kit), [Pipecat](/integrations/agent-framework/pipecat), and the [Vercel AI SDK](/integrations/sdks-libraries/vercel-ai-sdk) have first party plugins. The full list is on the [Integrations](/integrations/agent-framework/live-kit) tab.

## Limits, errors, and regions

* [Concurrency and Limits](/api-reference/concurrency-and-limits) covers per plan concurrency and rate limits.
* [Error reference](/models/troubleshooting/error-reference) lists every status code the model endpoints return.
* East Asian streaming languages on Pulse are served from the US region at `wss://api.us.smallest.ai`. See the [Pulse model card](/model-cards/speech-to-text/pulse).