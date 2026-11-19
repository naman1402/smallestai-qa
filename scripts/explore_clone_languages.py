#!/usr/bin/env python3
"""Exploratory: what does an English-recorded clone do in other languages?

For each case, the clone and a native catalog voice say the same text. Both clips are transcribed
with Smallest's Pulse STT and scored against the input text (character similarity, 0-1). The catalog
voice is the baseline, so a low clone score means the clone (not the STT) lost the content.
We judge engineering behavior (status, errors, length, intelligibility vs baseline), not how it sounds.

Docs claims checked (docs/reference/smallest-docs-2026-11-18/):
  cross-lingual cloning supported, accent retained (models__voice-cloning__best-practices.md)
  native script required; Indic and Global language groups, cross-group "undefined behavior"
  (model-cards__text-to-speech__lightning-v-3-1.md, Code-Switching + Voice Cloning)

Usage: .venv/bin/python scripts/explore_clone_languages.py [--sample samples/my_voice.wav]
Creates 2 clones (Pro + Standard). The API cannot delete clones (finding C1): delete them in the dashboard.
Audio lands in out/clone-xlang/, results in out/clone-xlang/results.json. Every call is in evidence/.
"""

import argparse
import difflib
import json
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from smallest_qa.config import ROOT
from smallest_qa.utils import audio
from smallest_qa.utils.evidence import RUN_ID, set_test
from smallest_qa.utils.http import request
from smallest_qa.waves import cloning, tts
from smallest_qa.waves.payloads import DROP, PRO_MODEL, V31_MODEL, tts_body

OUT = ROOT / "out" / "clone-xlang"
RATE = 24000

# id: (text, TTS language (DROP = omit), STT language, Pro catalog baseline voice, note)
CASES = {
    "en": ("The train to the airport leaves at nine thirty from platform four.", "en", "en", "kelsey", ""),
    "es": ("El tren al aeropuerto sale a las nueve y media desde el andén cuatro.", "es", "es", "sofia", "Global"),
    "fr": ("Le train pour l'aéroport part à neuf heures trente du quai quatre.", "fr", "fr", "manon", "Global"),
    "de": ("Der Zug zum Flughafen fährt um halb zehn von Gleis vier ab.", "de", "de", "hanna", "Global"),
    "hi": ("हवाई अड्डे की ट्रेन साढ़े नौ बजे प्लेटफॉर्म चार से निकलती है।", "hi", "hi", "rhea", "Indic+Global"),
    "ta": ("விமான நிலையத்திற்கான ரயில் ஒன்பதரை மணிக்கு நான்காவது நடைமேடையில் இருந்து புறப்படுகிறது.", "ta", "ta",
           "malar", "Indic"),
    "ja": ("空港行きの電車は九時半に四番線から出発します。", "ja", "ja", "aria", "Pro only"),
    "zh": ("去机场的火车九点半从四号站台出发。", "zh", "zh", "hazel", "Pro only"),
    # edge cases a customer hits without reading the fine print
    "hi_latin_script": ("Airport ki train saadhe nau baje platform chaar se nikalti hai.", "hi", "hi", "rhea",
                        "docs: native script required"),
    "hi_text_language_en": ("हवाई अड्डे की ट्रेन साढ़े नौ बजे प्लेटफॉर्म चार से निकलती है।", "en", "hi", "rhea",
                            "language code does not match text"),
    "es_language_omitted": ("El tren al aeropuerto sale a las nueve y media desde el andén cuatro.", DROP, "es",
                            "sofia", "no language field"),
    "hinglish": ("मेरी meeting कल सुबह दस बजे है, please remind me.", "hi", "hi", "rhea", "code-switching"),
    "ta_plus_fr": ("ரயில் ஒன்பதரை மணிக்கு புறப்படுகிறது, et le bus part à dix heures.", DROP, "ta", "malar",
                   "cross-group: docs say undefined"),
}
STANDARD_CASES = ["es", "hi", "ta", "ja", "ta_plus_fr"]  # ja is not in lightning_v3.1's 20 languages


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[\W_]+", "", text)


def similarity(expected: str, heard: str) -> float:
    return round(difflib.SequenceMatcher(None, norm(expected), norm(heard)).ratio(), 2)


def transcribe(wav: bytes, language: str, label: str) -> dict:
    ex = request("POST", "/waves/v1/stt/", params={"model": "pulse", "language": language},
                 headers={"Content-Type": "audio/wav"}, data=wav, label=label)
    body = ex.json if isinstance(ex.json, dict) else {}
    return {"status": ex.status, "text": body.get("transcription", ""), "request_id": ex.request_id,
            "error": None if ex.status == 200 else ex.body[:200].decode("utf-8", "replace")}


def speak(voice: str, model: str, case_id: str, who: str) -> dict:
    text, lang, stt_lang, _, _ = CASES[case_id]
    body = tts_body(text=text, voice_id=voice, model=model, language=lang, output_format="wav", sample_rate=RATE)
    ex = tts.synthesize(body, label=f"xlang-{who}-{case_id}")
    row = {"status": ex.status, "request_id": ex.request_id}
    if ex.status != 200:
        return {**row, "error": ex.body[:200].decode("utf-8", "replace")}
    (OUT / f"{who}_{case_id}.wav").write_bytes(ex.body)
    seconds = audio.duration(ex.body, RATE) or 0
    heard = transcribe(ex.body, stt_lang, f"xlang-stt-{who}-{case_id}")
    return {**row, "seconds": seconds, "chars_per_s": round(len(text) / seconds, 1) if seconds else None,
            "heard": heard["text"], "similarity": similarity(text, heard["text"]),
            "stt_request_id": heard["request_id"], "stt_error": heard["error"]}


def make_clone(sample: Path, pool: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "clip.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(sample), "-ac", "1", "-ar", "24000",
                        "-t", "12", str(clip)], check=True)
        fields = {"model": "lightning-v3.1-pro"} if pool == "pro" else {}
        ex = cloning.create(clip, name=f"qa-xlang-{pool}-{RUN_ID}", language="en", **fields)
    vid = cloning.voice_id(ex)
    if not vid:
        raise SystemExit(f"clone create failed: {ex}")
    print(f"created {pool} clone {vid} ({ex.request_id})")
    return vid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=str(ROOT / "samples" / "my_voice.wav"))
    args = ap.parse_args()
    set_test("explore-clone-languages")
    OUT.mkdir(parents=True, exist_ok=True)

    clones = {"pro": make_clone(Path(args.sample), "pro"), "standard": make_clone(Path(args.sample), "standard")}
    results = {"clones": clones, "cases": {}}
    for case_id, (_, lang, _, baseline, note) in CASES.items():
        row = {"language": None if lang is DROP else lang, "note": note,
               "baseline": speak(baseline, PRO_MODEL, case_id, f"catalog-{baseline}"),
               "clone_pro": speak(clones["pro"], PRO_MODEL, case_id, "clone-pro")}
        if case_id in STANDARD_CASES:
            row["clone_standard"] = speak(clones["standard"], V31_MODEL, case_id, "clone-standard")
        results["cases"][case_id] = row
        cells = [f"{k}={v.get('status')}/{v.get('similarity', '-')}/{v.get('seconds', '-')}s"
                 for k, v in row.items() if isinstance(v, dict)]
        print(f"{case_id:22} {' '.join(cells)}")
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nresults: {OUT / 'results.json'}\nclones to delete in the dashboard: {list(clones.values())}")


if __name__ == "__main__":
    main()
