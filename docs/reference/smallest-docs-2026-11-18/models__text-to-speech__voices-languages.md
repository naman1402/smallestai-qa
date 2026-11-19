> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# AI Voices for Text to Speech: Voice IDs and Languages

> Browse the Lightning text to speech voice catalog: list voices with the API, filter by language and accent, and find the voice ID to pass in your requests.

Curated voice IDs you can paste straight into a TTS request, plus the API call for filtering the full catalog. The model cards remain the canonical source for the complete catalog - this page is the fastest path from "I need a voice" to "I have a `voice_id`".

> **Tip**
>
> **Pairing rule.** Standard Lightning v3.1 voice IDs only work with `"model": "lightning_v3.1"`, which will be [retired](/api-reference/deprecations/models) on Nov 30, 2026. Lightning v3.1 Pro voice IDs only work with `"model": "lightning_v3.1_pro"` or `"model": "lightning_v3.1_pro_10_26"` (the [preview checkpoint](/model-cards/text-to-speech/lightning-v-3-1-pro#checkpoints) for English, Spanish and Hindi). Mismatched pairing returns synthesised audio in the wrong voice or no audio at all. See the [Pro model card](/model-cards/text-to-speech/lightning-v-3-1-pro) and [v3.1 model card](/model-cards/text-to-speech/lightning-v-3-1) for the full catalogs.

## Quick pick by use case

| Use case                       | Recommended voice           | Model                | Why                                       |
| ------------------------------ | --------------------------- | -------------------- | ----------------------------------------- |
| US conversational, female      | `kaitlyn`                   | `lightning_v3.1_pro` | Pro pool, natural American accent         |
| US conversational, male        | `blake`                     | `lightning_v3.1_pro` | Pro pool, natural American accent         |
| UK conversational, female      | `sophie`                    | `lightning_v3.1_pro` | Pro pool, British accent                  |
| UK conversational, male        | `sam`                       | `lightning_v3.1_pro` | Pro pool, British accent                  |
| Indian English + Hindi, female | `meher`                     | `lightning_v3.1_pro` | Pro pool, Indian voices code-switch en↔hi |
| Indian English + Hindi, male   | `aviraj`                    | `lightning_v3.1_pro` | Pro pool, Indian voices code-switch en↔hi |
| Hindi                          | `ahan` (M) / `rhea` (F)     | `lightning_v3.1_pro` | Pro pool, pass `language: hi`             |
| Tamil                          | `mathan` (M) / `malar` (F)  | `lightning_v3.1_pro` | Pro pool, pass `language: ta`             |
| Spanish (Castilian)            | `marco` (M) / `candela` (F) | `lightning_v3.1_pro` | Pro pool, pass `language: es`             |

## Lightning v3.1 Pro - by accent + gender

Premium pool with a curated catalog. The accent pools below are English-focused; Indian Pro voices additionally code-switch to Hindi when `language: hi` is set (or `language` is omitted, defaulting to `en + hi`). The Pro pool also includes dedicated voices for 29 additional languages - 9 Indic, 8 Asian & Middle Eastern, 12 European (including Dutch and Swedish) - listed in the accordions below. Pass the matching ISO 639-1 code in the `language` body parameter, or use `auto` to route across all supported languages with any English/Hindi voice.

#### American (18 voices)

**Female:** `kaitlyn`, `savannah`, `amelia`, `zoe`, `ruby`, `leah`, `jenna`, `kate`, `molly`, `sara`, `fiona`

**Male:** `blake`, `austin`, `henry`, `jack`, `leo`, `luke`, `owen`

#### British (12 voices)

**Female:** `sophie`, `ellie`, `cressida`, `ottilie`, `elowen`, `seraphina`

**Male:** `sam`, `henry`, `benedict`, `cormac`, `rupert`, `finley`

#### Indian (13 voices - code-switch English + Hindi)

**Female:** `rhea`, `zariya`, `kareena`, `mishka`, `inaaya`, `saira`, `meher`, `aarini`

**Male:** `aviraj`, `vyom`, `zoravar`, `reyansh`, `ahan`

#### Indian languages (67 voices - 9 languages)

Pair each voice with its language code, e.g. `"language": "ta"` with a Tamil voice.

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

#### Asian & Middle Eastern languages (21 voices - 8 languages)

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

#### European languages (61 voices - 10 languages)

| Language               | Code | Female voices                                   | Male voices                             |
| ---------------------- | ---- | ----------------------------------------------- | --------------------------------------- |
| German                 | `de` | `hanna`, `lea`, `petra`                         | `max`, `ben`, `markus`, `finn`          |
| Spanish                | `es` | `martina`, `candela`, `irene`                   | `mateo`, `gabriel`, `marco`             |
| French                 | `fr` | `manon`, `juliette`, `lucie`, `elise`, `amelie` | `louis`, `nicolas`, `maxime`, `raphael` |
| Italian                | `it` | `silvia`, `concetta`, `arianna`                 | `davide`, `luca`, `leonardo`            |
| Portuguese (Brazilian) | `pt` | `juliana`, `leticia`                            | `gustavo`, `thiago`, `bruno`            |
| Portuguese (European)  | `pt` | `catarina`                                      | `francisco`                             |
| Russian                | `ru` | `anastasia`, `ekaterina`, `olga`, `irina`       | `andrei`, `nikolai`, `maksim`           |
| Greek                  | `el` | `katerina`, `dimitra`, `athina`                 | `dimitris`, `vasilis`                   |
| Finnish                | `fi` | `aino`, `helmi`, `venla`                        | `mika`, `timo`, `matti`                 |
| Norwegian              | `no` | `solveig`, `marit`                              | `kristian`, `espen`                     |
| Polish                 | `pl` | `ewa`, `joanna`                                 | `tomasz`, `jakub`                       |

See the [Pro model card voice catalog](/model-cards/text-to-speech/lightning-v-3-1-pro#voice-catalog) for ranking notes.

## Lightning v3.1 - standard pool

217 voices total across 12 languages - English (176), Hindi (115), Tamil (13), Spanish (11), Kannada (10), Marathi (9), Telugu (8), Odia (8), Punjabi (8), Malayalam (6), Gujarati (5), Bengali (4). Voices below are the curated short-list; the [v3.1 model card](/model-cards/text-to-speech/lightning-v-3-1#voice-catalog) has the full catalog.

#### English (American) - 20 voices

**Male:** `jordan`, `robert`, `johnny`, `lucas`, `magnus`, `ronald`, `blofeld`, `zorin`, `felix`, `malcolm`

**Female:** `lauren`, `hannah`, `vanessa`, `brooke`, `olivia`, `rachel`, `nicole`, `elizabeth`, `ilsa`, `christine`

#### English (other accents) - 3 voices

| Voice ID  | Gender | Accent     |
| --------- | ------ | ---------- |
| `william` | Male   | Canadian   |
| `erica`   | Female | Canadian   |
| `chloe`   | Female | Australian |

#### Indic (Hindi + Indian-English) - 21 voices

**Female:** `sunidhi`, `chinmayi`, `aanya`, `siya`, `anuja`, `avni`, `ishani`, `yuvika`, `advika`, `sana`, `sameera`, `srishti`, `sakshi`, `maya`

**Male:** `wasim`, `rehan`, `parth`, `atharv`, `vivaan`, `devansh`, `aarush`

#### Tamil - 2 voices

| Voice ID     | Gender |
| ------------ | ------ |
| `jeevan`     | Male   |
| `rajeshwari` | Female |

#### Telugu - 2 voices

| Voice ID  | Gender |
| --------- | ------ |
| `srihari` | Male   |
| `padmaja` | Female |

#### Kannada - 2 voices

| Voice ID    | Gender |
| ----------- | ------ |
| `pranav`    | Male   |
| `deepashri` | Female |

#### Malayalam - 2 voices

| Voice ID  | Gender |
| --------- | ------ |
| `vaisakh` | Male   |
| `shibi`   | Female |

#### Marathi - 2 voices

| Voice ID | Gender |
| -------- | ------ |
| `nilesh` | Male   |
| `rupali` | Female |

#### Gujarati - 2 voices

| Voice ID   | Gender |
| ---------- | ------ |
| `dhruvit`  | Male   |
| `niharika` | Female |

#### Spanish - 7 voices

| Voice ID   | Gender |
| ---------- | ------ |
| `marcos`   | Male   |
| `david`    | Male   |
| `miguel`   | Male   |
| `daniella` | Female |
| `camilla`  | Female |
| `alba`     | Female |
| `nerea`    | Female |

## Fetch the full catalog programmatically

For filtering by language, accent, gender or use case, query the live Pro catalog.

**`cURL`**

```bash cURL
curl "https://api.smallest.ai/waves/v1/lightning-v3.1-pro/get_voices" \
  -H "Authorization: Bearer $SMALLEST_API_KEY"
```

**`Python`**

```python Python
import os
import requests

response = requests.get(
    "https://api.smallest.ai/waves/v1/lightning-v3.1-pro/get_voices",
    headers={"Authorization": f"Bearer {os.environ['SMALLEST_API_KEY']}"},
)
response.raise_for_status()
voices = response.json()["voices"]

# Filter by language
english_voices = [v for v in voices if "english" in v["tags"]["language"]]
print(f"{len(english_voices)} English voices")

# Filter by accent
indian_voices = [v for v in voices if v["tags"].get("accent") == "indian"]
print(f"{len(indian_voices)} Indian-accent voices")

# Filter by gender
female_voices = [v for v in voices if v["tags"].get("gender") == "female"]
print(f"{len(female_voices)} female voices")

# Use a voice
voice_id = english_voices[0]["voiceId"]   # e.g. "kaitlyn"
print(f"Selected: {voice_id}")
```

**`JavaScript`**

```javascript JavaScript
const response = await fetch(
  "https://api.smallest.ai/waves/v1/lightning-v3.1-pro/get_voices",
  { headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` } }
);
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const { voices } = await response.json();

const english = voices.filter((v) => v.tags.language.includes("english"));
const indian  = voices.filter((v) => v.tags.accent === "indian");
const female  = voices.filter((v) => v.tags.gender === "female");

console.log(`${english.length} English, ${indian.length} Indian-accent, ${female.length} female`);
```

## Voice object shape

Each entry in the `voices` array has:

| Field           | Type      | Description                                                                       |
| --------------- | --------- | --------------------------------------------------------------------------------- |
| `voiceId`       | string    | Use this with the `voice_id` body field in synthesis requests.                    |
| `displayName`   | string    | Human-readable name.                                                              |
| `tags.language` | string\[] | Languages the voice was trained on (e.g., `["english"]`, `["english", "hindi"]`). |
| `tags.accent`   | string    | One of `american`, `british`, `indian`, `canadian`, `australian`.                 |
| `tags.gender`   | string    | `male` or `female`.                                                               |
| `tags.age`      | string    | `young`, `middle-aged`, `senior`.                                                 |
| `tags.usecases` | string\[] | Recommended use cases (e.g., `["conversational"]`, `["narration"]`).              |

## Supported languages

| Language                          | Code | v3.1 voices |    v3.1 Pro voices |
| --------------------------------- | ---- | ----------: | -----------------: |
| English (US, UK, Indian)          | `en` |         176 |                 43 |
| Hindi                             | `hi` |         115 | 13 (Indian voices) |
| Tamil                             | `ta` |          13 |                 12 |
| Spanish                           | `es` |          11 |                  6 |
| Kannada                           | `kn` |          10 |                 10 |
| Marathi                           | `mr` |           9 |                  6 |
| Telugu                            | `te` |           8 |                  8 |
| Odia                              | `or` |           8 |                  8 |
| Punjabi                           | `pa` |           8 |                  7 |
| Malayalam                         | `ml` |           6 |                  6 |
| Gujarati                          | `gu` |           5 |                  5 |
| Bengali                           | `bn` |           4 |                  5 |
| German                            | `de` |           - |                  7 |
| French                            | `fr` |           - |                  9 |
| Italian                           | `it` |           - |                  6 |
| Portuguese (Brazilian + European) | `pt` |           - |                  7 |
| Russian                           | `ru` |           - |                  7 |
| Greek                             | `el` |           - |                  5 |
| Finnish                           | `fi` |           - |                  6 |
| Norwegian                         | `no` |           - |                  4 |
| Polish                            | `pl` |           - |                  4 |
| Arabic                            | `ar` |           - |                  2 |
| Chinese (Mandarin)                | `zh` |           - |                  5 |
| Indonesian                        | `id` |           - |                  4 |
| Japanese                          | `ja` |           - |                  4 |
| Korean                            | `ko` |           - |                  1 |
| Malay                             | `ms` |           - |                  2 |
| Turkish                           | `tr` |           - |                  2 |
| Vietnamese                        | `vi` |           - |                  1 |

For per-language voice counts that always reflect the live catalog, query `GET /waves/v1/lightning-v3.1-pro/get_voices` and group by `tags.language`. For the canonical per-voice metadata, see the [Lightning v3.1 model card voice catalog](/model-cards/text-to-speech/lightning-v-3-1#voice-catalog) and [Lightning v3.1 Pro voice catalog](/model-cards/text-to-speech/lightning-v-3-1-pro#voice-catalog).

## Need Help?