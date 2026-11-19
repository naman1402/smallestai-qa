> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Lightning v3.1 Pro

> Model card for Lightning v3.1 Pro. Premium 44.1 kHz TTS pool with a curated voice catalog across American, British, and Indian accents, English + Hindi code-switching, 31 supported languages plus `auto` routing, and improved naturalness.

Latest Release

[`lightning_v3.1_pro_10_26`](#checkpoints) is in preview for English, Spanish and Hindi until 2026-11-28.

Premium 44.1 kHz text to speech on dedicated capacity: curated Indian, British and American voices, Hindi code-switching, 31 languages. Same latency and limits as [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1). Start with the [quickstart](/models/text-to-speech/quickstart).

## Who it's for

* Voice agents and IVR where voice quality is the differentiator and the caller hears the brand.
* Products serving Indian, British and American English customers from one catalog, with Hindi code-switching.

## Model Overview

|                                 |                                                                                                                             |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Developed by**                | Smallest AI                                                                                                                 |
| **Model IDs**                   | `lightning_v3.1_pro` (stable), `lightning_v3.1_pro_10_26` (preview: English, Spanish, Hindi)                                |
| **Model type**                  | Text-to-Speech Websocket \| Text-to-Speech SSE \| Text-to-Speech HTTP                                                       |
| **Languages**                   | 31 - 10 Indic, 8 Asian & Middle Eastern, 13 European; plus `auto` routing. See [Supported Languages](#supported-languages). |
| **Audio Output formats**        | PCM, MP3, WAV, ulaw, alaw                                                                                                   |
| **Pricing (Standard Plan)**     | See the [pricing page](https://smallest.ai/pricing)                                                                         |
| **Concurrency (Standard Plan)** | 10                                                                                                                          |
| **Native Sample Rate**          | 44.1 kHz                                                                                                                    |
| **Supported sample rates**      | 8,000 / 16,000 / 24,000 / 44,100 Hz                                                                                         |
| **Audio channels**              | Mono                                                                                                                        |
| **Recommended GPU**             | NVIDIA L40S                                                                                                                 |
| **Max chunk size**              | 250 characters (optimal throughput at \~140 characters per request)                                                         |

## Checkpoints

### How checkpoints work

`lightning_v3.1_pro` always serves the current stable checkpoint. A dated ID such as `lightning_v3.1_pro_10_26` lets you try a new checkpoint during its 30-day preview, and the checkpoint may receive updates during that time; the [changelog](/changelog/lightning-v-3-1) lists them. When a preview is promoted, it becomes the stable `lightning_v3.1_pro` and the dated ID stays available for 30 more days. A new checkpoint can cover only some languages, and when it is promoted only those languages change. Enterprise customers who need more time can contact their account team to pin their current checkpoint.

> **What changes on 2026-11-28**
>
> For English (`en`), Spanish (`es`) and Hindi (`hi`) only, the `lightning_v3.1_pro_10_26` preview becomes the stable `lightning_v3.1_pro`. From then on, use `"model": "lightning_v3.1_pro"` for these languages. Requests that omit `language` default to `en + hi`, so they move too. `lightning_v3.1_pro_10_26` remains available for 30 more days, until 2026-12-28. The other 28 languages and `auto` stay on their current checkpoints, so their audio does not change and you don't need to do anything for them.

### `lightning_v3.1_pro` vs `lightning_v3.1_pro_10_26`

|                                        | `lightning_v3.1_pro`                                                                                                                                                     | `lightning_v3.1_pro_10_26`                                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Status**                             | Stable                                                                                                                                                                   | Preview until 2026-11-28                                                                                              |
| **Languages**                          | 31 (see [Supported Languages](#supported-languages))                                                                                                                     | 3: English (`en`), Spanish with English code-switching (`es`), Hindi with English code-switching (`hi`)               |
| **Quality**                            | Current Pro quality                                                                                                                                                      | New checkpoint for English, Spanish and Hindi; see [benchmarks](#lightning_v31_pro_10_26-vs-other-providers)          |
| **Voices**                             | Full Pro catalog                                                                                                                                                         | Full Pro catalog; see [Recommended voices](#recommended-voices-for-lightning_v31_pro_10_26)                           |
| **Features, endpoints, regions**       | HTTP, SSE, WebSocket; US and India                                                                                                                                       | Same                                                                                                                  |
| **Sample rates, pricing, concurrency** | See [Model Overview](#model-overview)                                                                                                                                    | Same as `lightning_v3.1_pro`                                                                                          |
| **`model` value**                      | `lightning_v3.1_pro`                                                                                                                                                     | `lightning_v3.1_pro_10_26`                                                                                            |
| **From 2026-11-28**                    | Becomes the stable model for `en`, `es`, `hi` and omitted `language`, serving the `lightning_v3.1_pro_10_26` checkpoint; the other 28 languages and `auto` are unchanged | Promoted to stable as `lightning_v3.1_pro` for English, Spanish and Hindi; this ID remains available until 2026-12-28 |

For any language other than English, Spanish or Hindi, use `lightning_v3.1_pro`.

### Try the preview

**`lightning_v3.1_pro_10_26 (preview)`**

```bash title="lightning_v3.1_pro_10_26 (preview)"
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{
    "text": "Hi, thanks for calling. How can I help you today?",
    "voice_id": "kelsey",
    "language": "en",
    "model": "lightning_v3.1_pro_10_26"
  }' --output speech.wav
```

---

## Key Capabilities

Ultra-low latency architecture designed for conversational AI and live streaming.

HTTP, SSE, and WebSocket transports for real-time playback.

`language: en` → UK + American accented English. `language: hi` → Indian accented English + Hindi (code-switching). Omit → defaults to `en + hi`. Plus 29 additional languages via dedicated Pro voices - pass the ISO 639-1 code (e.g. `ta`, `de`, `ja`), or use `auto` for cross-language routing.

Broadcast-quality 44.1 kHz audio with natural prosody, intonation, and conversational rhythm.

Premium voices across American, British, and Indian accents.

Custom pronunciation dictionaries for specialized vocabulary, brand names, and domain-specific terms.

---

## Performance & Benchmarks

Pro improves on standard Lightning v3.1 across accuracy, expressiveness, delivery, and MOS quality. Tables below pair Pro with the same competitor set documented on the [Lightning v3.1 model card](/model-cards/text-to-speech/lightning-v-3-1); refer to that card for Pro-vs-Standard comparisons. Open the accordion under each category to see what each metric measures.

> **Note**
>
> **Where 200 ms TTFB comes from.** Measured from a client in the same AWS region as the inference pool (India `ap-south-1`, USA `us-west-2`, geo-routed by client location). Client-to-server round-trip time adds on top. A naive test from a laptop far from either region typically reports 500-800 ms because RTT dominates synthesis time. For a production-realistic number, measure from your production network position, not your dev machine.

### Naturalness - higher is better

| Metric      | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| ----------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| Overall     |               3.16 |        3.13 |                  3.16 |                       3.17 |    3.20 |           3.07 |             3.28 |        3.17 |        3.06 |   3.02 |
| Naturalness |               2.55 |        2.41 |                  2.52 |                       2.55 |    2.57 |           2.42 |             2.58 |        2.57 |        2.41 |   2.37 |
| Intonation  |               3.06 |        3.06 |                  3.07 |                       3.06 |    3.12 |           2.90 |             3.28 |        3.04 |        2.91 |   2.86 |
| Prosody     |               2.81 |        2.73 |                  2.82 |                       2.86 |    2.83 |           2.65 |             3.09 |        2.76 |        2.61 |   2.58 |

#### What each Naturalness metric measures

* **Overall** - Holistic listener rating of how natural the voice sounds end-to-end.
* **Naturalness** - How human-like the voice sounds; penalizes robotic or synthetic quality.
* **Intonation** - Whether pitch rises and falls appropriately for the sentence type (question, statement, exclamation).
* **Prosody** - The broader umbrella of rhythm, stress, and melody, how well the voice "reads" the sentence as a human would.

### Expressiveness - higher is better

| Metric          | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| --------------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| Overall         |           **3.55** |        3.45 |                  3.44 |                       3.46 |    3.38 |           3.49 |             3.54 |        3.50 |        3.37 |   3.41 |
| Paralinguistics |           **3.64** |        3.60 |                  3.59 |                       3.61 |    3.56 |           3.60 |             3.64 |        3.58 |        3.55 |   3.58 |
| Emotions        |           **3.47** |        3.30 |                  3.28 |                       3.31 |    3.19 |           3.38 |             3.44 |        3.41 |        3.19 |   3.23 |

#### What each Expressiveness metric measures

* **Overall** - Holistic listener rating of how expressive the voice sounds given the context of the sentence.
* **Paralinguistics** - Non-verbal vocal elements like laughter, sighs, or filler sounds ("um", "uh") and whether they're rendered appropriately.
* **Emotions** - How accurately the voice conveys the intended emotional tone (neutral, warm, urgent, etc.).

### Delivery - higher is better

| Metric                | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| --------------------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| Boundary Consistency  |               4.96 |        4.94 |                  4.93 |                       4.95 |    4.93 |           4.88 |             4.99 |        4.77 |        4.90 |   4.88 |
| Pronunciation Style   |               4.98 |        4.96 |                  4.95 |                       4.96 |    4.96 |           4.93 |             4.99 |        4.91 |        4.94 |   4.89 |
| Natural Pace          |           **4.72** |        4.57 |                  4.51 |                       4.51 |    4.01 |           4.23 |             4.66 |        4.47 |        4.33 |   3.74 |
| Pause Placement       |           **4.66** |        4.54 |                  4.49 |                       4.51 |    4.28 |           4.34 |             4.59 |        4.41 |        4.38 |   4.09 |
| Breathing Naturalness |           **3.82** |        3.06 |                  3.14 |                       3.14 |    2.79 |           2.88 |             3.43 |        3.28 |        2.77 |   2.42 |

#### What each Delivery metric measures

* **Boundary Consistency** - Whether phrase and sentence boundaries are marked consistently with pauses or pitch shifts, without arbitrary breaks mid-phrase.
* **Pronunciation Style** - Not just correctness, but stylistic choices i.e., formal vs. casual register, regional accent consistency, honorific handling.
* **Natural Pace** - Whether the speaking rate feels comfortable and appropriate for the content type, neither rushed nor dragging.
* **Pause Placement** - Whether silences appear at semantically correct points (after commas, between clauses) rather than mid-word or mid-phrase.
* **Breathing Naturalness** - Whether breath sounds occur at realistic points and with realistic frequency, not absent entirely or inserted randomly.

### Accuracy

Mixed direction - WER, CER, Hallucination, and Deletion are *lower is better*; Pronunciation % is *higher is better*.

#### Whisper jiwer

| Metric                        | Direction | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| ----------------------------- | --------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| WER                           | lower     |              1.36% |       1.26% |                 1.35% |                      1.33% |   1.43% |          1.26% |            1.37% |       1.25% |       1.10% |  2.83% |
| CER                           | lower     |          **0.40%** |       0.52% |                 0.60% |                      0.54% |   0.59% |          0.62% |            0.61% |       0.50% |       0.47% |  1.16% |
| Hallucination                 | lower     |          **0.00%** |       0.07% |                 0.08% |                      0.01% |   0.06% |          0.04% |            0.01% |       0.06% |       0.00% |  0.22% |
| Deletion                      | lower     |          **0.00%** |       0.14% |                 0.17% |                      0.18% |   0.16% |          0.24% |            0.18% |       0.15% |       0.12% |  0.33% |
| Pronunciation % Whisper jiwer | higher    |             98.68% |      98.94% |                98.90% |                     98.87% |  98.79% |         99.02% |           98.82% |      98.95% |      99.02% | 97.72% |

#### Whisper LLM

| Metric                      | Direction | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| --------------------------- | --------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| WER                         | lower     |              0.96% |       0.82% |                 0.72% |                      0.57% |   0.88% |          0.70% |            0.72% |       0.60% |       0.55% |  2.15% |
| CER                         | lower     |              0.34% |       0.30% |                 0.28% |                      0.21% |   0.30% |          0.35% |            0.33% |       0.23% |       0.18% |  1.03% |
| Hallucination               | lower     |          **0.00%** |       0.07% |                 0.07% |                      0.00% |   0.02% |          0.02% |            0.01% |       0.03% |       0.00% |  0.10% |
| Pronunciation % Whisper LLM | higher    |             99.04% |      99.25% |                99.35% |                     99.43% |  99.14% |         99.32% |           99.29% |      99.43% |      99.45% | 97.95% |

#### What each Accuracy metric measures

* **WER (Word Error Rate)** - Percentage of words in the transcript that differ from the reference; measures how faithfully the TTS renders the input text.
* **CER (Character Error Rate)** - Like WER but at the character level.
* **Hallucination** - Words or sounds the TTS generates that have no basis in the input text. Insertions, substitutions, or fabricated content.
* **Deletion** - Words from the reference text that the TTS dropped entirely.
* **Pronunciation %** - The proportion of words pronounced correctly out of total words.
* **Whisper jiwer vs Whisper LLM** - Two judging methodologies. `jiwer` uses raw Whisper-decoded transcripts; LLM-judged uses a follow-on LLM to normalize transcription noise. Both report the same metric family; LLM-judged tends to give lower error rates by reducing false positives from punctuation/casing.

### MOS v2 - higher is better

| Metric   | Lightning v3.1 Pro | GPT-4o-mini | ElevenLabs Turbo v2.5 | ElevenLabs Multilingual v2 | Sonic-3 | Gemini 2.5 Pro | Gemini 2.5 Flash | MAI-Voice-1 | Inworld 1.5 | S2 Pro |
| -------- | -----------------: | ----------: | --------------------: | -------------------------: | ------: | -------------: | ---------------: | ----------: | ----------: | -----: |
| Mean MOS |               4.22 |        4.16 |                  3.98 |                       4.02 |    3.76 |           4.11 |             4.24 |        3.97 |        3.73 |   3.99 |
| UTMOS    |           **3.76** |        3.76 |                  3.37 |                       3.41 |    2.77 |           3.57 |             3.71 |        3.33 |        2.54 |   3.50 |
| WV-MOS   |           **5.05** |        4.55 |                  4.60 |                       4.63 |    4.76 |           4.65 |             4.76 |        4.62 |        4.91 |   4.48 |

### Per-language head-to-head vs MiniMax speech-2.8-hd

Per-language advantage of Lightning v3.1 Pro over MiniMax speech-2.8-hd, male/female voices averaged per language. Emergent Win % is the share of samples where at least one AI judge preferred Lightning; the Advantage columns are the score margin above zero (higher is better; a negative value means MiniMax won that metric on that language).

| Language      | Emergent Win % | Acc-LLM Advantage | Acc-jiwer Advantage | WV-MOS Advantage | Audiobox-CE Advantage | Audiobox-PQ Advantage |
| ------------- | -------------: | ----------------: | ------------------: | ---------------: | --------------------: | --------------------: |
| Greek         |             85 |              0.92 |                0.34 |             0.31 |                  0.22 |                  0.14 |
| Swedish       |             84 |              2.26 |                2.57 |             0.14 |                  0.31 |                  0.25 |
| Dutch         |             82 |              0.17 |                0.14 |             0.29 |                  0.07 |                  0.16 |
| Norwegian     |             82 |              2.01 |                0.07 |             0.10 |                  0.21 |                  0.18 |
| English US    |             76 |              0.22 |                0.38 |             0.30 |                  0.20 |                  0.28 |
| Finnish       |             69 |              0.61 |                1.44 |             0.15 |                  0.35 |                  0.14 |
| English UK    |             69 |              0.36 |                0.43 |             0.30 |                  0.15 |                  0.15 |
| German        |             66 |              0.18 |                0.11 |             0.44 |                  0.37 |                  0.30 |
| Korean        |             62 |              0.20 |                0.09 |             0.02 |                  0.33 |                  0.28 |
| Arabic        |             61 |              0.17 |                0.37 |             0.33 |                  0.15 |                  0.28 |
| Turkish       |             61 |              0.23 |                0.11 |             0.08 |                  0.26 |                  0.40 |
| Russian       |             58 |              0.08 |                0.22 |             0.59 |                  0.37 |                  0.24 |
| Spanish LatAm |             56 |              0.31 |                0.08 |             0.27 |                  0.26 |                  0.20 |
| Indonesian    |             56 |              0.25 |                0.26 |             0.36 |                  0.24 |                  0.42 |
| Malay         |             56 |              0.34 |                0.17 |             0.44 |                  0.12 |                  0.08 |
| Hindi         |             55 |              0.07 |                0.28 |             0.43 |                  0.17 |                  0.13 |
| Japanese      |             55 |             11.21 |                9.80 |             0.09 |                  0.28 |                  0.13 |
| Chinese       |             54 |              0.17 |                9.20 |             0.11 |                  0.10 |                  0.17 |
| French        |             53 |              0.07 |                0.27 |             0.26 |                  0.20 |                  0.10 |
| Portuguese    |             51 |              0.41 |                0.14 |             0.13 |                  0.10 |                  0.03 |
| Italian       |             46 |              0.15 |               -0.01 |             0.21 |                  0.08 |                 -0.03 |
| Polish        |             46 |              0.11 |                0.26 |             0.22 |                  0.33 |                  0.07 |
| **ALL**       |         **63** |          **0.93** |            **1.21** |         **0.25** |              **0.22** |              **0.19** |

#### What each column measures

* **Emergent Win %** - How often listeners preferred Lightning v3.1 Pro over MiniMax speech-2.8-hd when hearing both say the same thing. Above 50 = Lightning won more often than not. Scores averaged over a male and a female voice per language.
* **Acc-LLM Advantage** - How many fewer word mistakes per hundred words compared to MiniMax, judged with a language-aware LLM. Positive = ours is more accurate.
* **Acc-jiwer Advantage** - Same as Acc-LLM, but the word mistakes are counted automatically by software (`jiwer`) rather than an LLM. Positive = ours is more accurate.
* **WV-MOS Advantage** - Difference in overall sound quality, rated automatically by a quality-prediction model (WV-MOS). Positive = ours sounds cleaner.
* **Audiobox-CE Advantage** - Difference in how pleasant and enjoyable the audio is to listen to (Content Enjoyment score). This score matches human opinions best in our testing. Positive = ours is more enjoyable.
* **Audiobox-PQ Advantage** - Difference in recording/production quality (e.g. how clean and professional the audio sounds). Positive = ours is cleaner.

> **Note**
>
> On Norwegian, Swedish, and Malay, MiniMax does not have native voices for these languages, so its English voices were used to speak them. The test sentences for these three languages were also machine-translated from English.

#### What each MOS metric measures

* **Mean MOS** - Mean Opinion Score: average listener rating on a 1–5 scale across the test set; the canonical aggregate quality metric in TTS evaluation.
* **UTMOS** - A predicted MOS from the UTMOS reference model - an automated proxy for subjective quality.
* **WV-MOS** - A predicted MOS from the WavLM-based WV-MOS reference model - another automated proxy commonly reported alongside UTMOS for cross-validation.

Want to reproduce these results? See the [TTS evaluation script](/model-cards/text-to-speech/tts-evaluation-script) to measure TTFB and synthesis quality in your own environment.

### lightning_v3.1_pro_10_26 vs other providers

Each value is the share of judged comparisons that the `lightning_v3.1_pro_10_26` preview checkpoint won against that provider, with male and female voices combined. 50% is on par and higher favours Lightning; N/A means that provider has no voice for the language.

| Competitor             | English (US) | English (UK) | Spanish (LATAM) | Hindi | Average |
| ---------------------- | -----------: | -----------: | --------------: | ----: | ------: |
| ElevenLabs v4 Turbo    |        48.9% |        43.4% |           57.4% | 53.5% |   50.8% |
| Cartesia Sonic 3.6     |        55.1% |        54.3% |           57.4% | 47.9% |   53.7% |
| Gemini 3.8 Flash TTS   |        54.3% |        47.0% |           58.5% | 61.9% |   55.4% |
| Fish Drama 3           |        55.7% |        57.1% |           79.5% | 72.3% |   66.1% |
| Fish S2.1 Pro          |        90.4% |        85.4% |           92.8% | 96.6% |   91.3% |
| Inworld TTS-2          |        75.8% |        66.4% |           82.4% | 84.0% |   77.1% |
| MiniMax Speech 2.8 HD  |        82.5% |        71.2% |           84.6% | 85.1% |   80.8% |
| OpenAI gpt-4o-mini-tts |      88.8% † |          N/A |           98.4% | 92.3% |   93.2% |
| Gnani Timbre v2.5      |          N/A |          N/A |             N/A | 66.5% |   66.5% |
| Gnani Timbre v3.0      |          N/A |          N/A |             N/A | 66.8% |   66.8% |
| Sarvam Bulbul v4 Flash |          N/A |          N/A |             N/A | 80.5% |   80.5% |

† OpenAI US English: clean sentences only.

---

## Supported Languages

Pass the `language` body parameter to steer the Pro pool's output:

| `language` value                                                     | Behaviour                                                                                            |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `en`                                                                 | UK + American accented English. Best paired with British or American Pro voices.                     |
| `hi`                                                                 | Indian accented English + Hindi (mid-utterance code-switching). Best paired with Indian Pro voices.  |
| ISO 639-1 code of an additional Pro language (e.g. `ta`, `de`, `ja`) | Native synthesis in that language. Pair with a Pro voice from that language's catalog section below. |
| *omitted*                                                            | Defaults to `en + hi` - mixed Indian + Western English coverage.                                     |

### Additional Pro languages

29 additional languages have dedicated Pro voices. Pass the ISO 639-1 code in the `language` body parameter and pick a `voice_id` from the matching [Voice Catalog](#voice-catalog) section. Pass `auto` to route across all supported languages using any English or Hindi voice.

**Indic** - 9 languages

| Language  | Code | Pro voices |
| --------- | ---- | ---------: |
| Marathi   | `mr` |          6 |
| Tamil     | `ta` |         12 |
| Malayalam | `ml` |          6 |
| Telugu    | `te` |          8 |
| Kannada   | `kn` |         10 |
| Punjabi   | `pa` |          7 |
| Bengali   | `bn` |          5 |
| Odia      | `or` |          8 |
| Gujarati  | `gu` |          5 |

**Asian & Middle Eastern** - 8 languages

| Language           | Code | Pro voices |
| ------------------ | ---- | ---------: |
| Arabic             | `ar` |          2 |
| Chinese (Mandarin) | `zh` |          5 |
| Indonesian         | `id` |          4 |
| Japanese           | `ja` |          4 |
| Korean             | `ko` |          1 |
| Malay              | `ms` |          2 |
| Turkish            | `tr` |          2 |
| Vietnamese         | `vi` |          1 |

**European** - 12 languages

| Language                          | Code | Pro voices |
| --------------------------------- | ---- | ---------: |
| German                            | `de` |          7 |
| Spanish                           | `es` |          6 |
| French                            | `fr` |          9 |
| Italian                           | `it` |          6 |
| Dutch                             | `nl` |          - |
| Swedish                           | `sv` |          - |
| Portuguese (Brazilian + European) | `pt` |          7 |
| Russian                           | `ru` |          7 |
| Greek                             | `el` |          5 |
| Finnish                           | `fi` |          6 |
| Norwegian                         | `no` |          4 |
| Polish                            | `pl` |          4 |

Dutch and Swedish accept the codes on Pro; voice-count data pending as new Pro voice trains for those roll out.

For other languages, use the standard [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1) model (20 accepted codes; 12 with a trained voice catalog).

---

## Voice Catalog

The Pro voice catalog is distinct from standard Lightning v3.1. Voices below are listed in recommended ranking per accent group.

### Recommended voices for lightning_v3.1_pro_10_26

Every Pro voice works on the preview checkpoint. These give the best results, listed best first.

| Language     | Code | Female voices                                         | Male voices                                     |
| ------------ | ---- | ----------------------------------------------------- | ----------------------------------------------- |
| English (US) | `en` | `kelsey`, `ruby`, `autumn`, `savannah`, `zoe`         | `spencer`, `tucker`, `austin`, `nolan`, `blake` |
| English (UK) | `en` | `bethany`, `ellie`                                    | `henry`, `callum`                               |
| Spanish      | `es` | `sofia`, `regina`, `isabela`, `carolina`, `alejandra` | `rafael`, `adrian`, `hugo`, `ivan`, `lorenzo`   |
| Hindi        | `hi` | `rhea`, `mishka`, `meher`, `zariya`, `inaaya`         | `ahan`, `vyom`, `aviraj`, `zoravar`, `reyansh`  |

### Indian - Female

| Voice ID  | Name    |
| --------- | ------- |
| `rhea`    | Rhea    |
| `zariya`  | Zariya  |
| `kareena` | Kareena |
| `mishka`  | Mishka  |
| `inaaya`  | Inaaya  |
| `saira`   | Saira   |
| `meher`   | Meher   |
| `aarini`  | Aarini  |

### Indian - Male

| Voice ID  | Name    |
| --------- | ------- |
| `aviraj`  | Aviraj  |
| `vyom`    | Vyom    |
| `zoravar` | Zoravar |
| `reyansh` | Reyansh |
| `ahan`    | Ahan    |

### British - Female

| Voice ID    | Name      |
| ----------- | --------- |
| `sophie`    | Sophie    |
| `ellie`     | Ellie     |
| `cressida`  | Cressida  |
| `ottilie`   | Ottilie   |
| `elowen`    | Elowen    |
| `seraphina` | Seraphina |

### British - Male

| Voice ID   | Name     |
| ---------- | -------- |
| `sam`      | Sam      |
| `henry`    | Henry    |
| `benedict` | Benedict |
| `cormac`   | Cormac   |
| `rupert`   | Rupert   |
| `finley`   | Finley   |

### American - Female

| Voice ID   | Name     |
| ---------- | -------- |
| `kaitlyn`  | Kaitlyn  |
| `savannah` | Savannah |
| `amelia`   | Amelia   |
| `zoe`      | Zoe      |
| `ruby`     | Ruby     |
| `leah`     | Leah     |
| `jenna`    | Jenna    |
| `kate`     | Kate     |
| `molly`    | Molly    |
| `sara`     | Sara     |
| `fiona`    | Fiona    |

### American - Male

| Voice ID | Name   |
| -------- | ------ |
| `blake`  | Blake  |
| `austin` | Austin |
| `henry`  | Henry  |
| `jack`   | Jack   |
| `leo`    | Leo    |
| `luke`   | Luke   |
| `owen`   | Owen   |

### Indian Languages - 67 voices

Pair each voice with its matching `language` code (e.g. `"language": "ta"` with a Tamil voice).

| Language  | Code | Female voices                             | Male voices                                                                             |
| --------- | ---- | ----------------------------------------- | --------------------------------------------------------------------------------------- |
| Marathi   | `mr` | `mrunal`, `manasi`, `ketaki`, `tejaswini` | `mandar`, `tushar`                                                                      |
| Tamil     | `ta` | `malar`, `nila`, `tamilselvi`             | `mathan`, `dinesh`, `prabhu`, `ezhil`, `kavin`, `tamizh`, `barath`, `sakthi`, `murugan` |
| Malayalam | `ml` | `parvathy`, `lakshmi`                     | `vishnu`, `sreenath`, `unni`, `aravindan`                                               |
| Telugu    | `te` | `sravani`, `swathi`                       | `naveen`, `charan`, `sasank`, `bhaskar`, `gopal`, `manohar`                             |
| Kannada   | `kn` | `spoorthi`, `rashmi`, `varsha`, `sahana`  | `rakshith`, `kishore`, `yogesh`, `gowtham`, `shankar`, `basava`                         |
| Punjabi   | `pa` | `jasleen`, `manmeet`                      | `rajdeep`, `tejinder`, `sukhdeep`, `amrit`, `gagandeep`                                 |
| Bengali   | `bn` | -                                         | `rajib`, `tanmoy`, `subhro`, `arghya`, `indranil`                                       |
| Odia      | `or` | `sasmita`, `ankita`                       | `subrat`, `debasish`, `sambit`, `pratik`, `rakesh`, `smruti`                            |
| Gujarati  | `gu` | `krupa`, `riddhi`                         | `jignesh`, `mit`, `keval`                                                               |

### Asian & Middle Eastern Languages - 21 voices

| Language           | Code | Female voices           | Male voices              |
| ------------------ | ---- | ----------------------- | ------------------------ |
| Arabic             | `ar` | `layla`                 | `adam`                   |
| Chinese (Mandarin) | `zh` | `hazel`, `vivian`       | `dylan`, `silas`, `eli`  |
| Indonesian         | `id` | `nora`                  | `bryce`, `miles`, `cole` |
| Japanese           | `ja` | `aria`, `mila`, `daisy` | `jasper`                 |
| Korean             | `ko` | `june`                  | -                        |
| Malay              | `ms` | `sasha`                 | `roman`                  |
| Turkish            | `tr` | -                       | `beau`, `wes`            |
| Vietnamese         | `vi` | -                       | `kai`                    |

### European Languages - 61 voices

| Language               | Code | Female voices                                   | Male voices                             |
| ---------------------- | ---- | ----------------------------------------------- | --------------------------------------- |
| German                 | `de` | `hanna`, `lea`, `petra`                         | `max`, `ben`, `markus`, `finn`          |
| Spanish                | `es` | `martina`, `ines`, `paula`                      | `sebastian`, `mateo`, `gabriel`         |
| French                 | `fr` | `manon`, `juliette`, `lucie`, `elise`, `amelie` | `louis`, `nicolas`, `maxime`, `raphael` |
| Italian                | `it` | `silvia`, `concetta`, `arianna`                 | `davide`, `luca`, `leonardo`            |
| Portuguese (Brazilian) | `pt` | `juliana`, `leticia`                            | `gustavo`, `thiago`, `bruno`            |
| Portuguese (European)  | `pt` | `catarina`                                      | `francisco`                             |
| Russian                | `ru` | `anastasia`, `ekaterina`, `olga`, `irina`       | `andrei`, `nikolai`, `maksim`           |
| Greek                  | `el` | `katerina`, `dimitra`, `athina`                 | `dimitris`, `vasilis`                   |
| Finnish                | `fi` | `aino`, `helmi`, `venla`                        | `mika`, `timo`, `matti`                 |
| Norwegian              | `no` | `solveig`, `marit`                              | `kristian`, `espen`                     |
| Polish                 | `pl` | `ewa`, `joanna`                                 | `tomasz`, `jakub`                       |

> **Tip**
>
> Need a voice not in this list? Use the standard [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1) catalog (217 voices, more languages). Pass `"model": "lightning_v3.1"` (or omit the field) instead of `lightning_v3.1_pro`. Both pools support voice cloning.

---

## API Reference

### Endpoints

| Endpoint                                    | Method     | Use Case                     |
| ------------------------------------------- | ---------- | ---------------------------- |
| `https://api.smallest.ai/waves/v1/tts`      | POST       | Synchronous synthesis        |
| `https://api.smallest.ai/waves/v1/tts/live` | POST (SSE) | Server-sent events streaming |
| `wss://api.smallest.ai/waves/v1/tts/live`   | WebSocket  | Real-time streaming          |

See [Synthesize Speech](/api-reference/models/text-to-speech/synthesize-speech) for the full request/response schema, supported parameters, and error codes. To route to the Pro pool you must set `model` to `lightning_v3.1_pro` (or `lightning_v3.1_pro_10_26` for the preview checkpoint: English, Spanish, Hindi) explicitly - the field is optional but defaults to standard Lightning v3.1.

#### [Quickstart](/models/text-to-speech/quickstart)

Generate your first audio in under a minute with a single API call.

---

## Best Practices

### Voice ID + model pairing

Pair Pro voice IDs above with `"model": "lightning_v3.1_pro"` (or `"model": "lightning_v3.1_pro_10_26"` for the preview checkpoint). The API does not currently reject mismatched pairings, but pairing a Pro voice with `"model": "lightning_v3.1"` (or omitting `model`) can produce wrong or hallucinated audio. Server-side validation is on the roadmap.

### Language selection

* **`language: en`** → UK + American accented English. Pair with British or American Pro voices for best results.
* **`language: hi`** → Indian accented English + Hindi with native code-switching mid-utterance. Pair with Indian Pro voices.
* **Any additional Pro language** (e.g. `language: ta`, `language: de`, `language: ja`) → native synthesis in that language. Always pair with a Pro voice from that language's [Voice Catalog](#voice-catalog) section.
* **Omit `language`** → defaults to `en + hi`. Sensible when you don't know the input language ahead of time.

Per-voice metadata still lives in `tags.language` on the voice catalog (`GET /waves/v1/lightning-v3.1/get_voices`). The body parameter sets the *target* language for the synthesis pass; the voice ID controls the timbre and accent of the speaker.

### Text Formatting

* **Chunk boundaries.** Segment input at natural prosodic boundaries (`.` `!` `?` `,`). Maximum chunk size is 250 characters; optimal throughput at 140 characters per request.
* **Script integrity.** Use native script for each language. Mixed-script input within a single language token produces unpredictable phoneme mappings.
* **Lexicon overrides.** Use [pronunciation dictionaries](/models/text-to-speech/pronunciation-dictionaries) for domain-specific terms, brand names, and acronyms where default grapheme-to-phoneme conversion is insufficient.

For comprehensive text formatting rules (numeric handling, date/time, symbols, chunking logic), see [TTS Best Practices](/models/text-to-speech/best-practices).

---

## Use Cases

| Direct Use                             | Downstream Use                     |
| -------------------------------------- | ---------------------------------- |
| Voice assistants and conversational AI | Multi-turn conversational agents   |
| Interactive chatbots with voice output | Audio content generation pipelines |
| Real-time narration and live streaming | Telephony and IVR systems          |
| Accessibility tools and screen readers | Podcast generation                 |
| Customer service automation            |                                    |

---

## FAQ

#### How is Lightning v3.1 Pro different from standard Lightning v3.1?

Pro runs on dedicated inference capacity, isolated from general Lightning traffic, and ships a curated premium voice catalog with improved naturalness. Concurrency, latency, and rate-limit ceilings are identical to standard [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1) - the difference is voice quality and the catalog.

#### How do I route requests to the Pro pool?

Set `model` to `lightning_v3.1_pro` explicitly. The field is optional, but it defaults to standard Lightning v3.1 - for Pro you must pass it on every request.

#### Can I pair any voice with the Pro model?

Pair Pro voice IDs with `"model": "lightning_v3.1_pro"`. The API does not currently reject mismatched pairings, but pairing a Pro voice with `"model": "lightning_v3.1"` (or omitting `model`) can produce wrong or hallucinated audio. Server-side validation is on the roadmap.

#### Does Lightning v3.1 Pro support voice cloning?

Yes. Pass `model: lightning-v3.1-pro` to the [voice-cloning API](/models/voice-cloning/instant-clone-api) to clone onto the Pro pool, then use the resulting `voice_id` with TTS `model: lightning_v3.1_pro`. The default is `lightning-v3.1`.

#### Which languages does Lightning v3.1 Pro support?

Set `language: en` for UK + American accented English, or `language: hi` for Indian accented English + Hindi with native code-switching. Omitting `language` defaults to `en + hi`.

#### Are word-level timestamps supported on Pro voices?

Pro shares the Lightning v3.1 base-queue voices for English + Hindi (`meher`, `devansh`, `kartik`, `maithili`, `liam`, `avery`), so word events emit on those. Other Pro-only voices fall back to silent graceful degradation - audio is normal, but no word events are emitted.

#### What is lightning_v3.1_pro_10_26?

It is a new Lightning v3.1 Pro checkpoint for English (`en`), Spanish with English code-switching (`es`) and Hindi with English code-switching (`hi`), in preview until 2026-11-28. Try it by passing `"model": "lightning_v3.1_pro_10_26"` with one of those `language` values. Every Pro voice works on it; the [recommended voices](#recommended-voices-for-lightning_v31_pro_10_26) give the best results. On 2026-11-28, it becomes the stable `lightning_v3.1_pro` for English, Spanish and Hindi only, including requests that omit `language`, so use `"model": "lightning_v3.1_pro"` from then on. `lightning_v3.1_pro_10_26` remains available for 30 more days, until 2026-12-28. See [Checkpoints](#checkpoints).

#### Will my integration change on 2026-11-28?

Only if you call `lightning_v3.1_pro` with `language` set to `en`, `es` or `hi`, or without `language`. On 2026-11-28, the `lightning_v3.1_pro_10_26` preview becomes the stable `lightning_v3.1_pro` for English, Spanish and Hindi, and those requests start using it, so test `lightning_v3.1_pro_10_26` before then. You don't need to change the `model` value. If you are already calling `lightning_v3.1_pro_10_26`, switch to `lightning_v3.1_pro` by 2026-12-28; the preview ID remains available for 30 days after promotion. Enterprise customers who need more time can contact their account team to pin their current checkpoint.

#### I use other languages or auto on lightning_v3.1_pro. Does anything change?

No. Only English, Spanish and Hindi move to the new checkpoint. All other languages and `auto` stay on their current checkpoints, and no action is needed.

---

## Safety & Compliance

### Known Limitations

* **Larger, curated catalog on standard v3.1.** The Pro catalog is intentionally smaller. For the widest voice selection and more languages, use standard [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1).

> **Warning**
>
> Lightning v3.1 Pro must **not** be used for impersonation or fraud, generating deceptive audio content (deepfakes), creating content that violates consent or privacy, harassment or abuse, or any illegal or unethical purposes.

### Compliance

* No retention of synthesized audio
* Usage monitoring for policy compliance
* Enterprise plans can stop input text being stored, expire it after a window, or expire a single request with the `x-expire-content` header. See [Zero Data Retention](/models/enterprise/zero-data-retention)

For compliance documentation (GDPR, SOC2, HIPAA), contact [support@smallest.ai](mailto:support@smallest.ai).

---

## Support