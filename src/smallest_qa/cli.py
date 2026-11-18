"""`sqa`: a playground for trying the API by hand. Every call is logged to evidence/ like the tests.

    sqa voices [--model lightning-v3.1-pro]
    sqa tts "Hello there" [--voice meher --model lightning_v3.1_pro --format wav --rate 24000 --speed 1.0]
    sqa tts-ws "Hello there" [--voice …]
    sqa clones list | create FILE --name NAME [--model lightning-v3.1-pro --language en] | delete VOICE_ID
    sqa token [--ttl 300]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from smallest_qa.config import ROOT, settings
from smallest_qa.utils import audio
from smallest_qa.waves import auth, cloning, tts, voices
from smallest_qa.waves.payloads import PRO_MODEL, PRO_VOICE, tts_body, ws_payload

OUT = ROOT / "out"


def _save(name: str, data: bytes) -> Path:
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    path.write_bytes(data)
    return path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="sqa", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("voices")
    v.add_argument("--model", default="lightning-v3.1-pro")

    for name in ("tts", "tts-ws"):
        t = sub.add_parser(name)
        t.add_argument("text")
        t.add_argument("--voice", default=PRO_VOICE)
        t.add_argument("--model", default=PRO_MODEL)
        t.add_argument("--rate", type=int, default=24000)
        t.add_argument("--speed", type=float, default=1.0)
        if name == "tts":
            t.add_argument("--format", default="wav", choices=["wav", "mp3", "pcm", "ulaw", "alaw"])

    c = sub.add_parser("clones")
    csub = c.add_subparsers(dest="action", required=True)
    csub.add_parser("list")
    cc = csub.add_parser("create")
    cc.add_argument("file", type=Path)
    cc.add_argument("--name", required=True)
    cc.add_argument("--model", default="lightning-v3.1-pro")
    cc.add_argument("--language", default="en")
    cd = csub.add_parser("delete")
    cd.add_argument("voice_id")

    k = sub.add_parser("token")
    k.add_argument("--ttl", type=int, default=300)

    a = p.parse_args(argv)
    if not settings.api_key:
        sys.exit("set SMALLEST_API_KEY in .env (copy .env.example)")

    if a.cmd == "voices":
        ex = voices.list_voices(a.model)
        ids = voices.voice_ids(ex)
        print(f"{ex}\n{len(ids)} voices: {', '.join(ids[:40])}{' …' if len(ids) > 40 else ''}")
    elif a.cmd == "tts":
        ex = tts.synthesize(tts_body(text=a.text, voice_id=a.voice, model=a.model, sample_rate=a.rate,
                                     speed=a.speed, output_format=a.format))
        print(ex)
        if ex.status == 200:
            print(f"saved {_save(f'tts.{a.format}', ex.body)}  wav={audio.wav_info(ex.body)}")
    elif a.cmd == "tts-ws":
        tl = asyncio.run(tts.synthesize_ws(ws_payload(text=a.text, voice_id=a.voice, model=a.model,
                                                      sample_rate=a.rate, speed=a.speed)))
        print(f"first_chunk={tl.first_chunk_ms} ms  complete={tl.complete_ms}  chunks={tl.chunks}  "
              f"errors={tl.error_frames}")
        if tl.audio:
            seconds = audio.pcm_duration(len(tl.audio), a.rate)
            print(f"saved {_save('tts-ws.pcm', tl.audio)}  ({seconds} s of 16-bit PCM)")
    elif a.cmd == "clones":
        if a.action == "list":
            ex = cloning.list_clones()
            rows = (ex.json or {}).get("data", []) if isinstance(ex.json, dict) else []
            print(ex.status, json.dumps([{k: c.get(k) for k in ("voiceId", "displayName", "status", "modelIds")}
                                         for c in rows], indent=1))
        elif a.action == "create":
            ex = cloning.create(a.file, name=a.name, model=a.model, language=a.language)
            print(ex, "\nvoiceId:", cloning.voice_id(ex))
        else:
            print(cloning.delete(a.voice_id))
    elif a.cmd == "token":
        ex = auth.mint({"ttl_seconds": a.ttl})
        meta = {k: v for k, v in (ex.json or {}).items() if k != "access_token"} if isinstance(ex.json, dict) else ex
        print(ex.status, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
