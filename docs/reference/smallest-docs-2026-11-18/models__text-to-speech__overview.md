> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Lightning Text to Speech API: Low Latency, 31 Languages

> Lightning text to speech API: 44.1 kHz audio at ~200 ms time to first byte, 31 languages plus auto routing, streaming over HTTP, SSE or WebSocket, and voice cloning.

The Lightning TTS API converts text into natural speech via `https://api.smallest.ai/waves/v1`. 31 languages across two pools - the standard 217-voice Lightning v3.1 catalog (20 accepted codes, 12 with trained voices) and the premium Lightning v3.1 Pro pool (all 31) - plus `auto` for cross-language routing, at 44.1 kHz native sample rate, \~200ms TTFB, with sync, SSE, and WebSocket streaming.

**Hear Lightning v3.1 Pro** (voice: `meher`, model: `lightning_v3.1_pro`):

#### [Quickstart](/models/text-to-speech/quickstart)

Generate your first audio in under a minute.

#### [Streaming](/models/text-to-speech/streaming)

Audio chunks over WebSocket as they are generated.

## Synthesis Modes

Choose the synthesis mode that best fits your application's needs:

#### [Synchronous](/models/text-to-speech/sync-async)

Generate complete audio files with a single HTTP request. Ideal for pre-rendering content, batch processing, and applications where immediate streaming isn't required.

#### [Streaming](/models/text-to-speech/streaming)

Receive audio chunks as they're generated via WebSocket. Perfect for real-time voice assistants, live narration, and low-latency conversational AI.

## Available Models

#### [Lightning v3.1 Pro](/model-cards/text-to-speech/lightning-v-3-1-pro)

Premium curated voices, Hindi code-switching, 31 languages. `"model": "lightning_v3.1_pro"`. [New checkpoint in preview for English, Spanish and Hindi](/model-cards/text-to-speech/lightning-v-3-1-pro#checkpoints).

#### [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1)

217 voices, 12 languages with catalogs, instant cloning. `"model": "lightning_v3.1"`. Retiring Nov 30, 2026.

> **Warning**
>
> `lightning_v3.1` will be retired on Nov 30, 2026 (18:30 UTC). Move to `lightning_v3.1_pro` before then. See [Deprecation notices](/api-reference/deprecations/models).

## Feature Highlights

#### Ultra-Low Latency

Optimized streaming pipeline delivers \~200ms time-to-first-byte (TTFB) for real-time applications. Lightning v3.1 achieves even faster response times for conversational AI.

#### Voice Cloning

Create custom voice profiles by uploading audio samples. Instant voice cloning works with just a few seconds of audio, while professional voice cloning delivers studio-quality results.

#### 31 Languages + \`auto\` routing

Lightning v3.1 accepts 20 language codes (10 European: English, Spanish, French, German, Italian, Dutch, Swedish, Portuguese, Polish, Russian + 10 Indic: Hindi, Marathi, Gujarati, Punjabi, Bengali, Odia, Tamil, Telugu, Kannada, Malayalam). Its trained voice catalog covers 12 of these directly; the other 8 route via English or Hindi voices. Lightning v3.1 Pro covers all 31 languages with dedicated voices (adds Greek, Finnish, Norwegian + 8 Asian & Middle Eastern languages). Pass `auto` to route across any supported language using any English or Hindi voice. See the [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1#supported-languages) and [Lightning v3.1 Pro](/model-cards/text-to-speech/lightning-v-3-1-pro#additional-pro-languages) model cards for per-language voice counts.

#### Multiple Output Formats

Choose from PCM, WAV, MP3, or μ-law encoding. Configurable sample rates from 8kHz to 44kHz to match your application's requirements.

#### Speed Control

Adjust speech rate with a simple multiplier. Slow down for clarity or speed up for faster content delivery without pitch distortion.

#### Pronunciation Dictionaries

Define custom pronunciations for brand names, technical terms, and acronyms via the `pronunciation_dicts` parameter. Works on synchronous, SSE, and WebSocket requests alike, ensuring consistent, accurate pronunciation across all synthesized audio.

#### High-Quality Audio

Lightning v3.1 produces 44 kHz audio with natural prosody and expressiveness. Perfect for audiobooks, podcasts, and premium voice experiences.

#### WebSocket Streaming

Persistent connections for continuous audio streaming. Ideal for voice bots and interactive applications where latency is critical.

## Supported Languages

<table>
  <thead>
    <tr>
      <th>
        Language
      </th>

      <th>
        Code
      </th>

      <th>
        Lightning v3.1
      </th>

      <th>
        Lightning v3.1 Pro
      </th>
    </tr>
  </thead>

  <tbody>
    <tr>
      <td>
        English
      </td>

      <td>
        `en`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Hindi
      </td>

      <td>
        `hi`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes (Indian voices)
      </td>
    </tr>

    <tr>
      <td>
        Tamil
      </td>

      <td>
        `ta`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Kannada
      </td>

      <td>
        `kn`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Malayalam
      </td>

      <td>
        `ml`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Telugu
      </td>

      <td>
        `te`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Gujarati
      </td>

      <td>
        `gu`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Marathi
      </td>

      <td>
        `mr`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Bengali
      </td>

      <td>
        `bn`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Punjabi
      </td>

      <td>
        `pa`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Odia
      </td>

      <td>
        `or`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Spanish
      </td>

      <td>
        `es`
      </td>

      <td>
        Yes
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        German
      </td>

      <td>
        `de`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        French
      </td>

      <td>
        `fr`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Italian
      </td>

      <td>
        `it`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Portuguese
      </td>

      <td>
        `pt`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Russian
      </td>

      <td>
        `ru`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Greek
      </td>

      <td>
        `el`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Finnish
      </td>

      <td>
        `fi`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Norwegian
      </td>

      <td>
        `no`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Polish
      </td>

      <td>
        `pl`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Arabic
      </td>

      <td>
        `ar`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Chinese (Mandarin)
      </td>

      <td>
        `zh`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Indonesian
      </td>

      <td>
        `id`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Japanese
      </td>

      <td>
        `ja`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Korean
      </td>

      <td>
        `ko`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Malay
      </td>

      <td>
        `ms`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Turkish
      </td>

      <td>
        `tr`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>

    <tr>
      <td>
        Vietnamese
      </td>

      <td>
        `vi`
      </td>

      <td>
        \-
      </td>

      <td>
        Yes
      </td>
    </tr>
  </tbody>
</table>

> **Note**
>
> **Pro language support is per voice.** Indian Pro voices (e.g., `meher`, `rhea`, `aviraj`) speak English with native Hindi code-switching. British and American Pro voices speak English only. Each additional Pro language has its own dedicated voices - pass the matching ISO 639-1 `language` code with a voice from that language (see the [Pro voice catalog](/model-cards/text-to-speech/lightning-v-3-1-pro#voice-catalog)). For languages without Pro voices, use standard Lightning v3.1.

> **Tip**
>
> For per-language voice counts, see the [Lightning v3.1 model card](/model-cards/text-to-speech/lightning-v-3-1#supported-languages).

## Explore

#### [Quickstart](/models/text-to-speech/quickstart)

First API call in 60 seconds

#### [Streaming](/models/text-to-speech/streaming)

Real-time audio via WebSocket

#### [Voice Cloning](/models/voice-cloning/instant-clone-ui)

Clone from 5-15 seconds of audio

#### [Cookbook](https://github.com/smallest-inc/cookbook/tree/main/text-to-speech)

20+ open-source examples on GitHub

#### [Showcase](https://showcase.smallest.ai/)

See what developers have built

#### [Model Card](/model-cards/text-to-speech/lightning-v-3-1)

Lightning v3.1 specs and benchmarks

## FAQ: Lightning text to speech

**Which languages does the text to speech API support?**
Lightning v3.1 accepts 20 language codes and Lightning v3.1 Pro covers all 31 supported languages. Pass `auto` to route across any supported language. The [table above](#supported-languages) lists every code per model.

**How fast is the text to speech API?**
About 200 ms time to first byte, measured at 40 concurrent requests. Streaming delivers the first audio chunk while the rest is still being generated. See [Streaming](/models/text-to-speech/streaming).

**Can I stream audio instead of waiting for the full file?**
Yes. Choose HTTP for complete files, SSE or WebSocket for chunked real-time audio. [Choosing a transport](/models/text-to-speech/choosing-a-transport) compares the three.

**Can I use my own voice?**
Yes. Instant voice cloning works from a 5 to 15 second sample; the cloned voice ID then works in any synthesis request. See the [voice cloning API](/models/voice-cloning/instant-clone-api).

**Which audio formats can it return?**
PCM, WAV, MP3, or mu-law, at sample rates from 8 kHz up to the native 44.1 kHz.