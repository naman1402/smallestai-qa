"""Voice catalog and languages: does the API offer what the model cards promise?

Contract: docs/reference/smallest-docs-2026-11-18/
  model-cards__text-to-speech__lightning-v-3-1-pro.md  "Voice Catalog" tables (voice IDs per language code)
  api-reference__models__text-to-speech__get-waves-voices.md  voiceId, displayName, tags.language
A customer picks a voice from the docs and pastes its ID; one that is missing or tagged with
another language fails in production, not in the docs.
"""

import re

import pytest

from smallest_qa.config import ROOT
from smallest_qa.utils import audio
from smallest_qa.waves import tts, voices
from smallest_qa.waves.payloads import PRO_MODEL, PRO_VOICE, tts_body

DOCS = ROOT / "docs" / "reference" / "smallest-docs-2026-11-18"
PRO_CARD = DOCS / "model-cards__text-to-speech__lightning-v-3-1-pro.md"


def _section(path, start: str, end: str) -> str:
    text = path.read_text()
    return text[text.index(start) : text.index(end, text.index(start))]


def documented_pro_voices() -> dict[str, set[str]]:
    """{voice_id: {language codes}} from the Pro card's catalog. Accent tables (no code column) are en/hi."""
    out: dict[str, set[str]] = {}
    for row in _section(PRO_CARD, "## Voice Catalog", "## API Reference").splitlines():
        if not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        code = re.fullmatch(r"`([a-z]{2})`", cells[1]) if len(cells) > 1 else None
        for vid in re.findall(r"`([a-z]{3,})`", "|".join(cells[2:] if code else cells[:1])):
            out.setdefault(vid, set()).update({code.group(1)} if code else {"en", "hi"})
    return out


# API tags.language holds names ("german"), the docs list ISO codes
NAMES = {"en": "english", "hi": "hindi", "mr": "marathi", "ta": "tamil", "ml": "malayalam", "te": "telugu",
         "kn": "kannada", "pa": "punjabi", "bn": "bengali", "or": "odia", "gu": "gujarati", "ar": "arabic",
         "zh": "chinese", "id": "indonesian", "ja": "japanese", "ko": "korean", "ms": "malay", "tr": "turkish",
         "vi": "vietnamese", "de": "german", "es": "spanish", "fr": "french", "it": "italian", "nl": "dutch",
         "sv": "swedish", "pt": "portuguese", "ru": "russian", "el": "greek", "fi": "finnish", "no": "norwegian",
         "pl": "polish"}


def _languages(voice: dict) -> set[str]:
    lang = (voice.get("tags") or {}).get("language") or []
    return {str(x).lower() for x in (lang if isinstance(lang, list) else [lang])}


@pytest.fixture(scope="module")
def pro_catalog() -> dict[str, dict]:
    ex = voices.list_voices("lightning-v3.1-pro")
    assert ex.status == 200, ex
    items = ex.json.get("voices", []) if isinstance(ex.json, dict) else ex.json
    return {v.get("voiceId"): v for v in items if isinstance(v, dict)}


def test_documented_pro_voices_exist_with_their_language(pro_catalog):
    """Every voice in the Pro model card is in the API catalog, tagged with the language the card lists it under."""
    documented = documented_pro_voices()
    assert len(documented) > 100, "docs parse found too few voices; check the snapshot format"
    missing, wrong = [], {}
    for vid, codes in documented.items():
        if vid not in pro_catalog:
            missing.append(vid)
            continue
        tags = _languages(pro_catalog[vid])
        if not any(c in tags or any(t.startswith(NAMES.get(c, c)) for t in tags) for c in codes):
            wrong[vid] = {"docs": sorted(codes), "api": sorted(tags)}
    assert not missing and not wrong, (
        f"{len(missing)}/{len(documented)} documented voices missing: {sorted(missing)} | mis-tagged: {wrong}")


# One sentence per language family the Pro card claims "native synthesis" for, plus `auto` routing.
LANGS = [
    ("ja", "おはようございます。昨日の注文についてお電話しました。"),
    ("ta", "வணக்கம், நேற்று செய்த ஆர்டர் பற்றி அழைக்கிறேன்."),
    ("auto", "नमस्ते, मैं कल के ऑर्डर के बारे में कॉल कर रहा हूँ।"),  # docs: any English/Hindi voice + auto
]


@pytest.mark.parametrize("code,text", LANGS, ids=[c for c, _ in LANGS])
def test_documented_language_synthesizes_with_its_catalog_voice(code, text, pro_catalog):
    if code == "auto":
        vid = PRO_VOICE
    else:
        documented = [v for v, codes in documented_pro_voices().items() if code in codes]
        vid = next((v for v in documented if v in pro_catalog), None)
        assert vid, f"no {code} voice from the docs ({documented}) is in the API catalog"
    ex = tts.synthesize(tts_body(text=text, voice_id=vid, model=PRO_MODEL, language=code), label=f"tts-lang-{code}")
    assert ex.status == 200, ex
    seconds = audio.duration(ex.body, 24000)
    assert seconds and 1.5 <= seconds <= 12, f"{seconds} s for one sentence in {code} with {vid} | {ex}"
