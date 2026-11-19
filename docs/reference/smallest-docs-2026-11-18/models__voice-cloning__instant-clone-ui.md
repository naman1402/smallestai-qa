> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Clone a Voice in the Dashboard (No Code)

> Create an instant voice clone from a 5 to 15 second audio sample in the dashboard, no code required, and use it in Lightning text to speech.

Clone any voice from 5-15 seconds of reference audio using the web console. No code required. Upload a sample, preview the clone, and get a `voice_id` to use in your TTS API calls immediately.

## Prerequisites

* A [Smallest AI account](https://app.smallest.ai)
* A clean audio recording (5-15 seconds, `.mp3`, `.wav`, or `.mp4`)

For recording guidelines, see [Voice Cloning Best Practices](/models/voice-cloning/best-practices).

---

## Step 1: Navigate to Voice Cloning

Log in to [app.smallest.ai](https://app.smallest.ai/dashboard) and select **Voice Cloning** from the left sidebar under **Playground**.

![Smallest AI dashboard with Voice Cloning highlighted in the left sidebar](/_fern-files/_img/f7398f07a88c41748cbd176aeb2a801cf7172c9619c86103430cdce2a52a2e11.webp)

## Step 2: Start a New Clone

Click the **Create** button. If this is your first clone, the button is displayed in the center of the page. Otherwise, use the **Create** button in the top-right corner.

![Voice Cloning page showing the Create button](/_fern-files/_img/65ace9c02ab66d33c6c8fc9ef25814dc07b66939aaaaf8e57a549532f178bacf.webp)

A guide dialog appears with best practices for reference audio:

* **Use a quiet environment** to avoid background noise, hiss, or rumble.
* **Record clean, high-quality** reference audio of your natural speaking voice.
* **Speak normally.** The model captures timbre, accent, emotional tone, rhythm, and pacing automatically.

![Instant Voice Cloning guide showing recording best practices](/_fern-files/_img/d149391698738163169647cf91f3ffab3863015d41a974cb9cff94d23d8a76c1.webp)

Click **Next** to proceed.

## Step 3: Provide Reference Audio

Provide an audio clip of 5 to 15 seconds. Two options are available:

1. **Record Audio** - Record a live clip directly in the browser. Allow microphone access when prompted.
2. **Upload or drag and drop** - Upload a pre-recorded file. Supported formats: `.mp3`, `.wav`, `.mp4`.

The console provides a suggested text prompt to read aloud if you choose to record live.

![Add audio for cloning dialog showing Record Audio and upload options](/_fern-files/_img/725703d8e4bc6478adc668b0359a1c0208ca1d883a827846e4007b656dcb8928.webp)

## Step 4: Preview and Select Language

After uploading or recording, preview your audio using the playback controls. Select the target language(s) for the clone. English is selected by default; Hindi is also available.

For best results, record reference audio in the same language as your intended output. See [Voice Cloning Best Practices](/models/voice-cloning/best-practices) for multi-lingual cloning guidance.

![Language selection dialog showing English selected and Hindi available with audio preview](/_fern-files/_img/6cec3068119fd92258913f563d0a0f3620d2577e2c014dd8f74077f8dbd719bd.webp)

Click **Next** to proceed.

## Step 5: Listen to Clone Previews

The platform generates sample audio clips using your cloned voice. Listen to the previews to verify the voice matches your expectations. If the quality is not satisfactory, click **Back** to re-record or upload different reference audio.

![Voice clone preview dialog showing three generated audio samples with playback controls](/_fern-files/_img/9345c8b06f00da66eb73832db42d50df73b94ba7f54611b7b0c934ccf61d07d7.webp)

Click **Next** to proceed.

## Step 6: Name and Save

Provide a **Name**, **Tags**, and optional **Description** for the cloned voice. Accept the terms and conditions, then click **Finish** to save.

![Create a Voice Clone dialog showing name, tags, and description fields with Finish button](/_fern-files/_img/1db3603319897f8a234b133f212deb8016d69ae5f39e0f2930090140ab8803be.webp)

---

## Using Your Cloned Voice

After saving, the cloned voice appears in your Voice Cloning dashboard with its `voice_id`, type, tags, accent, and creation date.

![Voice Cloning dashboard listing cloned voices with name, type, tags, accent, and creation date](/_fern-files/_img/9d0e6a950c6cc89bf5d3093621e47d2e8c59ea7acc094041877dc259a778a8aa.webp)

Click the **Use** button next to your clone to open the Text to Speech playground with your cloned voice pre-selected.

![Voice Cloning dashboard with Use button highlighted for the cloned voice](/_fern-files/_img/1e94d8c73bd6866944091e8fa0503b1b5f24d4fa3b4ccad8fd7c74a0425b32d8.webp)

The TTS playground opens with your cloned voice selected under **Voice**, the model set to **Lightning v3.1**, and controls for pronunciation language, speed, and sample rate. Enter text and click **Generate** to synthesize speech with your cloned voice.

![Text to Speech playground showing cloned voice selected with model, language, speed, and sample rate controls](/_fern-files/_img/1220affe4ea1e80668aeb612fa8a01656fbcc5e478bb3c5ade8c0ef008d22958.webp)

---

## Using the Clone via API

Pass the `voice_id` from your dashboard in any TTS API call:

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is my cloned voice.",
    "voice_id": "voice_xsJ0rrvuqR",
    "model": "lightning_v3.1_pro"
  }' \
  -o output.pcm
```

For programmatic voice cloning (create clones via code), see [Voice Cloning via API](/models/voice-cloning/instant-clone-python-sdk).

Need help? Contact [support@smallest.ai](mailto:support@smallest.ai) or ask on [Discord](https://discord.gg/9WtSXv26WE).