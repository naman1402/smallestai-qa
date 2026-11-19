> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# API Reference

> Overview of the Smallest AI APIs: base URLs for the Voice Agents API and the Models API, authentication, SDK snippets, errors, and limits.

## Base URLs

| API                                             | Base URL                           | What it covers                                                                                                                                                |
| ----------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Voice Agents API](/api-reference/voice-agents) | `https://api.smallest.ai/atoms/v1` | Agents, versioning, calls, campaigns, audiences, phone numbers, knowledge bases, tools, webhooks, analytics, billing                                          |
| [Models API](/api-reference/models)             | `https://api.smallest.ai/waves/v1` | Lightning text to speech, Pulse speech to text, Hydra speech to speech, Electron chat completions, voice cloning, pronunciation dictionaries, usage analytics |

Both APIs use the same key. Send it as a bearer token on every request:

```bash
curl "https://api.smallest.ai/atoms/v1/agent" \
  -H "Authorization: Bearer $SMALLEST_API_KEY"
```

See [Authentication](/api-reference/authentication) to create a key, and [Concurrency and Limits](/api-reference/concurrency-and-limits) for what a plan allows.

## Reading the reference

Every endpoint page shows the request schema, the response schema, and a runnable snippet in cURL, Python, and TypeScript. The Python and TypeScript snippets use the official `smallestai` packages, so the code you copy matches the SDK method names.

To send a request from the docs, click **Try it** on an endpoint page and paste your API key into the **BearerAuth** field. Paste only the key, without `Bearer ` in front. You can create a key on the [API Keys](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=api-reference) page, and [Authentication](/api-reference/authentication#try-requests-in-the-api-playground) walks through it step by step.

WebSocket endpoints (realtime agent, streaming text to speech, realtime speech to text, Hydra) document the handshake, every message type in both directions, and the close codes.

## Errors

Error responses carry an HTTP status and a JSON body with a machine readable `error_type` or `code`. The per API error pages list every status and how to recover:

* [Voice Agents error reference](/voice-agents/resources/error-reference)
* [Models error reference](/models/troubleshooting/error-reference)

## Deprecations

Deprecated endpoints keep working and return a `Deprecation: true` header. The [Deprecations](/api-reference/deprecations/voice-agents) section lists each one with its migration target, and the [Agent Versioning migration guide](/api-reference/deprecations/agent-versioning-migration) covers the v1 to v2 change endpoint by endpoint.