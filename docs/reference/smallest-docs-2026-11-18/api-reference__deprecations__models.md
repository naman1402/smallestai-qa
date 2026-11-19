> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Deprecation Notices

> Index of Smallest AI model tags, endpoints, and parameters that are deprecated or scheduled for removal, with the migration target for each.

This page lists Models (Waves) surfaces that are deprecated. Each row shows the current status and the migration target.

## How to read this page

* **Deprecated**: the surface still works, but new integrations should use the migration target.
* **Rejects**: the surface returns an error and does not process the request. Migrate immediately.
* **Removed**: the surface no longer exists. Requests return `404`.
* **Scheduled**: still works; the change takes effect on the date shown.
* **Retiring**: still works until the retirement date shown, then is retired.

## Currently deprecated

### Speech-to-Speech (Hydra)

| Surface                                                | Deprecated since | Status                                                                                                                                                                                                | Migrate to                                                                                                                                                                                                                |
| ------------------------------------------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `?model=hydra` on `wss://api.smallest.ai/waves/v1/s2s` | 2026-08-20       | Deprecated. Session still opens, but the server emits a `warning` frame with `code: "model_deprecated"` immediately before `session.created`. The warning names `hydra-v1.0` as the migration target. | `?model=hydra-v1.1` (current release, recommended) or `?model=hydra-v1.0` (the tag the server's own warning points at). See the [Hydra model card](/model-cards/speech-to-speech/hydra) for the per-version voice roster. |

## Scheduled deprecation

### Lightning v3.1

| Surface                                                                                                                                                                                         | Takes effect         | Status                                                                                                                                                                                                                                                                                                       | Migrate to                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `lightning_v3.1`, including requests with no `model`; the `/waves/v1/lightning-v3.1/` routes (`get_speech`, `stream`, `get_speech/stream`, `get_voices`); voice clones made on `lightning-v3.1` | 2026-11-30 18:30 UTC | Retiring. After retirement, requests with `"model": "lightning_v3.1"` or no `model` will be served by `lightning_v3.1_pro`, so the voice and sound may change, and `lightning_v3.1_pro` becomes the default. The legacy routes will be retired, and voice clones made on `lightning-v3.1` will stop working. | `"model": "lightning_v3.1_pro"`. 1) Set it on every request to the unified routes. 2) Pick voices from `GET /waves/v1/lightning-v3.1-pro/get_voices`; the voice catalogs differ. 3) Create voice clones again with `"model": "lightning-v3.1-pro"` on `POST /waves/v1/voice-cloning`. 4) Python SDK users of `WavesStreamingTTS`: upgrade to `smallestai>=5.1.1`, since earlier versions call the legacy WebSocket route. Pro accepts every `language` code that `lightning_v3.1` accepts. |

### Lightning v3.1 Pro (EN, HI, and ES)

| Surface                                                                                               | Takes effect | Status                                                                                                                                                                                                                                                                                                   | Migrate to                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Current `lightning_v3.1_pro` checkpoint for `language` `en`, `es` or `hi`, or with `language` omitted | 2026-11-28   | Scheduled. On 2026-11-28, the `lightning_v3.1_pro_10_26` preview checkpoint becomes the stable `lightning_v3.1_pro` for English, Spanish and Hindi. Requests that omit `language` (default `en + hi`) move too. All other languages and `auto` stay on their current checkpoints and are not deprecated. | Keep using `"model": "lightning_v3.1_pro"`; no change to the `model` value is needed. Test with `"model": "lightning_v3.1_pro_10_26"` before 2026-11-28. Enterprise customers can contact their account team to pin their current checkpoint. See [Checkpoints](/model-cards/text-to-speech/lightning-v-3-1-pro#checkpoints). |
| `lightning_v3.1_pro_10_26` (preview model ID for English, Spanish and Hindi)                          | 2026-12-28   | Scheduled. Remains available for 30 days after it becomes the stable `lightning_v3.1_pro` on 2026-11-28.                                                                                                                                                                                                 | `"model": "lightning_v3.1_pro"`                                                                                                                                                                                                                                                                                               |

## Reporting a break

If a surface you rely on starts emitting a deprecation warning unexpectedly, or a mapping on this page looks wrong, open a ticket and quote the surface plus the exact server frame you received. That is the minimum needed to trace and reroute.