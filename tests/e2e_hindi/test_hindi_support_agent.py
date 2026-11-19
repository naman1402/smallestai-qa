"""End-to-end journeys of the branded support agent serving Hindi (and Hinglish) callers.

Same product as tests/e2e (src/smallest_qa/app), same thresholds, Hindi content: the brand voice is cloned from
the owner's English recording and speaks Hindi (cross-lingual cloning, voice-cloning best-practices.md), the
brand name gets a Hindi pronunciation dictionary, and replies mix Devanagari with English product words and carry
an order number, a DD/MM/YYYY date, a mobile number and a rupee amount (app/llm_hi.py).

What is new compared to the English suite:
  - every agent reply is transcribed back with Pulse (language=hi) after the call and judged by llm_hi.judge:
    words (loanwords in either script count), numbers, and whether the date was read day-first
  - the caller is a stock Hindi voice (conftest.hindi_callers), and how well Pulse understood it is scored
  - a sentence-boundary check: does the server release a Hindi sentence ending in a danda (।)?
    (continuations.md lists only `. ? ! …` as terminal punctuation)
  - a runaway guard on every agent utterance: audio far longer than its text (llm_hi.plausible_s) is scored as
    a blocker; a clone speaking Hindi has produced 128 s of audio for one sentence
  - the phone leg runs with what the web call taught: date_format=EU, and "." for "।" if the danda was not a
    boundary; the scorecard says which

Cost of one run: 1 clone (delete by hand, C1), ~1,250 TTS characters, 11 STT calls (+ retries on 429), 2 sockets.
English-suite medians over its 3 runs on 2026-11-19 (evidence/2026-11-19-e2e-runs.md) are in the check notes.
"""

import asyncio
import io
import statistics
import subprocess
import time
import wave

import pytest
from e2e.conftest import assert_journey, require_profile
from e2e.test_support_agent import RESPONSE_MS, TALK_OVER_S, TTFA_MS, _stt

from smallest_qa.app import llm_hi, phone
from smallest_qa.app.llm import BRAND, ScriptedLLM
from smallest_qa.app.llm_hi import SCRIPT, plausible_s, spoken
from smallest_qa.app.profile import VoiceProfile, prepare_sample, upload_clone, wait_ready
from smallest_qa.app.session import AgentSession
from smallest_qa.utils import audio, live
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import pronunciation, stt, tts
from smallest_qa.waves.payloads import DROP, tts_body

pytestmark = pytest.mark.clone

SIMILARITY = 0.6  # the English suite's preview threshold
BOUNDARY_MS = 1000  # a released sentence's first audio; a held one waits for the next fragment (2.5 s here)
EN_S_PER_CHAR = 0.065  # English-suite turns, e.g. 9.4 s for the 143-character first reply (run 53d78cbd)
EN = {"response_ms": 1299, "ttfa_ms": 314, "talk_over_s": 2.4, "after_barge_ms": 237, "phone_ms": 1287,
      "preview_sim": 0.96, "brand_delta_s": 0.72}  # English-suite medians, runs b3ede2aa / f0d2f3cf / 53d78cbd
BRAND_LINE = f"{BRAND} में आपका स्वागत है।"
DANDA_FIX = "stream '.' in place of '।' (the server ends a sentence only at . ? ! …)"


def _wav(pcm: bytes, rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _ulaw_decode(data: bytes) -> bytes:
    """G.711 mu-law -> 16-bit PCM: what the far end of the phone line hears."""
    out = bytearray()
    for b in data:
        b = ~b & 0xFF
        s = ((((b & 0x0F) << 3) + 0x84) << ((b >> 4) & 7)) - 0x84
        out += (-s if b & 0x80 else s).to_bytes(2, "little", signed=True)
    return bytes(out)


def _turn_rids(sock, turn) -> list[str]:
    """The turn's request ids in the order their audio arrived (one per released segment; TurnMetrics sorts them)."""
    return list(dict.fromkeys(f["request_id"] for f in sock.chunks_after(turn.first_sent_ms) if f.get("request_id")))


def _turn_pcm(sock, turn) -> bytes:
    return b"".join(bytes(sock.audio.get(rid, b"")) for rid in _turn_rids(sock, turn))


def _phone_line(wav16k: bytes) -> bytes:
    """Caller audio as it reaches us over a phone line: 8 kHz, through G.711 mu-law and back, as WAV."""
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(phone.RATE),
                          "-f", "s16le", "pipe:1"], input=wav16k, capture_output=True, check=True).stdout
    return _wav(_ulaw_decode(phone.mulaw_encode(pcm)), phone.RATE)


def _check_runaway(card, j: str, clips: list[tuple[str, float, str]], evidence=(), note: str = ""):
    """clips: (utterance, audio seconds, text spoken). Audio far longer than its text is a runaway generation."""
    bad = [f"{what}: {sec} s for {len(text)} chars" for what, sec, text in clips if sec > plausible_s(text)]
    worst = max((round(sec / max(len(text), 1), 3) for _, sec, text in clips), default=None)
    card.check(j, "agent audio length plausible for its text (no runaway generation)", bad or "none", not bad,
               f"<= {llm_hi.PER_CHAR_S} s/char + {llm_hi.SLACK_S} s", weight=3, blocker=True, evidence=evidence,
               note=f"worst {worst} s/char; English suite ~{EN_S_PER_CHAR} s/char" + (f"; {note}" if note else ""))


def _brand_seconds(dict_ids: list[str], label: str, voice: VoiceProfile) -> tuple[float, str]:
    ex = tts.synthesize(tts_body(text=BRAND_LINE, voice_id=voice.voice_id, model=voice.model,
                                 language="hi", output_format="wav", pronunciation_dicts=dict_ids or DROP),
                        label=label)
    return (audio.duration(ex.body, 24000) or 0.0) if ex.status == 200 else 0.0, ex.request_id


def _round_trips(items: list[tuple], label: str, brand_says: str | None) -> list[dict]:
    """After the call: each agent reply (Reply, WAV) -> Pulse language=hi -> llm_hi.judge."""
    out = []
    for k, (reply, wav) in enumerate(items):
        heard = None
        if len(wav) > 1000:
            time.sleep(1.2)  # Pulse STT limit
            heard, _ = _stt(wav, f"{label}-{k}", "hi")
        said = stt.text(heard) if heard else ""
        out.append({**llm_hi.judge(reply, said, brand_says), "heard": said, "stt_id": heard and heard.request_id})
    return out


def _score_round_trips(card, j: str, results: list[dict], date_workaround: str | None, setup: str):
    ids = [r["stt_id"] for r in results]
    sims = [r["similarity"] for r in results]
    card.check(j, "agent replies intelligible (Pulse hi round trip), worst reply", min(sims, default=None),
               bool(sims) and min(sims) >= SIMILARITY, f">= {SIMILARITY} STT similarity", weight=2, evidence=ids,
               note=f"per reply {sims}; English-suite scoring {[r['plain'] for r in results]} (no loanword "
                    f"aliases, numbers included); English preview median {EN['preview_sim']}; {setup}")
    nums = {k: v for r in results for k, v in r["entities"].items() if k != "date"}
    missed = [r["heard"][:160] for r in results if not all(v for k, v in r["entities"].items() if k != "date")]
    card.check(j, "numbers survive the round trip (order no., mobile, ₹ amount)", nums,
               bool(nums) and all(nums.values()), "every number read back", weight=2, evidence=ids,
               note="; ".join(f"heard: {h}" for h in missed))
    dated = next((r for r in results if "date" in r["entities"]), None)
    if dated:
        ok = dated["entities"]["date"]
        how = "5 December" if ok else "May 12 (US order)" if dated["month_first"] else "neither"
        card.check(j, "05/12/2026 read day-first (Indian convention)", how, ok, "5 December", weight=1,
                   workaround=None if ok else date_workaround, evidence=[dated["stt_id"]],
                   note=f"heard: {dated['heard'][:160]}")


# ---------------------------------------------------------------------------------------------------------------
def test_01_onboarding(state, scorecard, sample, tmp_path):
    """Brand clones its voice from the owner's English recording, previews it in Hindi, and adds a Hindi
    pronunciation for the brand name."""
    j = "onboarding (hi)"
    clip = prepare_sample(sample, tmp_path / "brand_voice.wav")
    vid, attempts = upload_clone(clip, name=f"qa-e2e-hi-{RUN_ID}")
    scorecard.check(j, "upload accepted with the browser's MIME label (audio/x-wav)", attempts[0].status,
                    attempts[0].status == 200, "200", workaround="re-label uploads as audio/wav before sending",
                    evidence=[a.request_id for a in attempts])
    scorecard.check(j, "clone created", bool(vid), bool(vid), "voice id returned", weight=3, blocker=True,
                    evidence=[attempts[-1].request_id],
                    note="clone language=en (the reference audio's, per create-voice-clone.md), speech language=hi")
    if not vid:
        assert_journey(scorecard, j)
    state["clone_ids"].append(vid)
    status, waited = wait_ready(vid)
    scorecard.check(j, "clone ready", f"{status} after {waited} s", status == "completed" and waited <= 30,
                    "completed within 30 s", weight=2, blocker=True)
    profile = VoiceProfile(voice_id=vid)
    state["profile"] = profile

    ex = tts.synthesize(tts_body(text=llm_hi.PREVIEW, voice_id=vid, model=profile.model, language="hi",
                                 output_format="wav"), label="e2e-hi-preview")
    time.sleep(1.2)  # Pulse STT limit
    heard, _ = _stt(ex.body, "e2e-hi-preview-stt", "hi") if ex.status == 200 else (None, None)
    said = stt.text(heard) if heard else ""
    preview_s = (audio.duration(ex.body, 24000) or 0.0) if ex.status == 200 else 0.0
    sim = stt.similarity(llm_hi.PREVIEW, said, llm_hi.LOANWORDS)
    scorecard.check(j, "Hindi preview intelligible (loanwords in either script)", sim,
                    ex.status == 200 and sim >= SIMILARITY, f">= {SIMILARITY} STT similarity",
                    evidence=[ex.request_id, heard and heard.request_id],
                    note=f"heard: {said}; English-suite scoring {stt.similarity(llm_hi.PREVIEW, said)}; "
                         f"English preview median {EN['preview_sim']}")

    d = pronunciation.create([{"word": BRAND, "pronunciation": llm_hi.BRAND_SAYS_HI}])
    dict_id = (d.json or {}).get("id") if isinstance(d.json, dict) else None
    plain, rid_plain = _brand_seconds([], "e2e-hi-brand-plain", profile)
    with_dict, rid_dict = _brand_seconds([dict_id] if dict_id else [], "e2e-hi-brand-dict", profile)
    clips = [("preview", preview_s, llm_hi.PREVIEW), ("brand, no dictionary", plain, BRAND_LINE),
             ("brand, Devanagari respelling", with_dict, spoken(BRAND_LINE, llm_hi.BRAND_SAYS_HI))]
    sane = plain <= plausible_s(BRAND_LINE)  # a runaway makes the length comparison meaningless
    applied = bool(dict_id) and sane and with_dict <= plausible_s(clips[2][2]) and with_dict - plain >= 0.4
    says, fallback, note = llm_hi.BRAND_SAYS_HI if applied else None, None, "" if sane else "runaway audio; "
    if dict_id and sane and not applied:  # is it the Devanagari respelling, or the dictionary in a Hindi request?
        up = pronunciation.update(dict_id, [{"word": BRAND, "pronunciation": llm_hi.BRAND_SAYS_LATIN}])
        latin, rid_latin = _brand_seconds([dict_id], "e2e-hi-brand-latin", profile)
        clips.append(("brand, Latin respelling", latin, spoken(BRAND_LINE, llm_hi.BRAND_SAYS_LATIN)))
        if up.status == 200 and latin - plain >= 0.4 and latin <= plausible_s(clips[-1][2]):
            says, fallback = llm_hi.BRAND_SAYS_LATIN, "write the respelling in Latin script"
        note = f"Latin respelling: {plain} s -> {latin} s ({rid_latin}); "
    scorecard.check(j, "brand dictionary applied in Hindi speech (Devanagari respelling)",
                    f"{plain} s -> {with_dict} s", applied, ">= +0.4 s with dictionary", weight=2,
                    workaround=fallback, evidence=[d.request_id, rid_plain, rid_dict],
                    note=note + f"English-suite median +{EN['brand_delta_s']} s")
    if dict_id:
        state["dict_id"] = dict_id
        if says:
            profile.dict_ids = [dict_id]
    state["brand_says"] = says
    _check_runaway(scorecard, j, clips, [ex.request_id, rid_plain, rid_dict])
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_02_web_call_with_barge_in(state, scorecard, hindi_callers):
    """A Hindi caller on the website: three turns (caller speaks -> Pulse hi -> scripted reply -> cloned voice),
    a barge-in on a long answer, a reply after it, then the danda sentence-boundary check. Replies are
    transcribed back after the call."""
    j = "web call (hi)"
    profile = require_profile(state)
    llm = ScriptedLLM()
    extra = {"language": "hi"}  # what the docs say to send for Hindi; no date_format (a first-time integrator)

    def msg(cid: str, text: str, more: bool) -> dict:
        m = {"context_id": cid, "voice_id": profile.voice_id, "model": profile.model, "sample_rate": 24000,
             "continue": more, "text": text, **extra}
        return m | ({"pronunciation_dicts": profile.dict_ids} if profile.dict_ids else {})

    async def call():
        turns, latencies, heard_caller, pcms = [], [], [], []
        async with live.live(label="e2e-hi-web-call") as sock:
            agent = AgentSession(sock, profile, extra=extra)
            pinger = asyncio.create_task(agent.keepalive())
            for n, (_, clip) in enumerate(hindi_callers):
                heard, _ = await asyncio.to_thread(_stt, clip, f"e2e-hi-web-stt-{n}", "hi")
                heard_caller.append(heard)
                start = sock.now()
                turn = await agent.finish(await agent.say(llm.stream(SCRIPT[n].text), f"qa-hi-web{n}-{RUN_ID}"))
                turns.append(turn)
                pcms.append(_turn_pcm(sock, turn))
                if turn.ttfa_ms is not None:
                    latencies.append((heard.total_ms or 0) + (turn.first_sent_ms - start) + turn.ttfa_ms)
                await asyncio.sleep(1.5)
            # barge-in: caller talks over a long answer about 1 s into the audio
            long_turn = await agent.say(llm.stream(llm_hi.INTERRUPTIBLE), f"qa-hi-web-barge-{RUN_ID}")
            first = await sock.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=long_turn.first_sent_ms)
            if first:
                await asyncio.sleep(1.0)
                await agent.interrupt(long_turn)
            long_turn = await agent.finish(long_turn)
            after = await agent.finish(await agent.say(llm.stream(llm_hi.AFTER_BARGE_IN), f"qa-hi-web-after-{RUN_ID}"))
            # sentence boundary: one sentence ending in a danda, the rest 2.5 s later. Released at the danda ->
            # audio well before the rest is sent; held -> only after it (or after max_buffer_delay_ms, 3 s)
            cid = f"qa-hi-boundary-{RUN_ID}"
            t1 = await sock.send(msg(cid, llm_hi.BOUNDARY_FIRST + "।", True))
            await asyncio.sleep(2.5)
            t2 = await sock.send(msg(cid, " " + llm_hi.BOUNDARY_REST, False))
            hit = await sock.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=t1)
            await sock.quiet(1.5, since=t2, timeout=30)
            boundary = (round(hit["t"] - t1) if hit else None, round(sock.audio_bytes_after(t1) / 48000, 2))
            pinger.cancel()
            return turns, latencies, heard_caller, pcms, long_turn, after, boundary, sock.closed_at, sock.errors()

    turns, latencies, heard_caller, pcms, barge, after, boundary, closed_at, errors = asyncio.run(call())
    ids = [t.request_ids[0] for t in turns if t.request_ids]

    danda, boundary_s = boundary
    danda_ok = danda is not None and danda <= BOUNDARY_MS
    state["danda_fix"] = fix = not danda_ok
    caller_sims = [stt.similarity(text, stt.text(h), llm_hi.ALIASES)
                   for (text, _), h in zip(hindi_callers, heard_caller, strict=True)]
    scorecard.check(j, "caller understood (Pulse hi, synthetic Hindi caller), worst turn", min(caller_sims),
                    min(caller_sims) >= SIMILARITY, f">= {SIMILARITY} STT similarity", weight=2,
                    evidence=[h.request_id for h in heard_caller],
                    note=f"per turn {caller_sims}; stock voice {llm_hi.CALLER_VOICE}, clean audio (a best case); "
                         "the English suite does not score caller STT")
    med = statistics.median(latencies) if latencies else None
    scorecard.check(j, "response latency (caller done -> agent audio), median", med and round(med),
                    bool(med) and med <= RESPONSE_MS, f"<= {RESPONSE_MS} ms", weight=3,
                    workaround=DANDA_FIX if fix else None, evidence=[heard_caller[0].request_id] + ids[:1],
                    note=f"per turn {[round(x) for x in latencies]} ms incl. Pulse hi; English median "
                         f"{EN['response_ms']} ms")
    ttfas = [t.ttfa_ms for t in turns if t.ttfa_ms is not None]
    ttfa = statistics.median(ttfas) if ttfas else None
    scorecard.check(j, "TTS first audio, median", ttfa, ttfa is not None and ttfa <= TTFA_MS, f"<= {TTFA_MS} ms",
                    weight=2, workaround=DANDA_FIX if fix else None, evidence=ids,
                    note=f"per turn {ttfas} ms (includes the scripted LLM finishing a 4-5 word first sentence, "
                         f"as in English); English median {EN['ttfa_ms']} ms")
    gaps = [t.min_headroom_s for t in turns]
    scorecard.check(j, "no audible gaps in agent speech", gaps, all(g is not None and g >= 0 for g in gaps),
                    "headroom >= 0 every turn", weight=3, evidence=ids)
    scorecard.check(j, "every turn answered", f"{len(ttfas)}/{len(turns)}", len(ttfas) == len(turns),
                    "all turns", weight=3, blocker=True, evidence=ids)

    results = _round_trips([(SCRIPT[n], _wav(pcm, 24000)) for n, pcm in enumerate(pcms)], "e2e-hi-web-rt",
                           state.get("brand_says"))
    _score_round_trips(scorecard, j, results, "send date_format: EU (or write the month as a word)",
                       "24 kHz, language=hi, no date_format")

    scorecard.check(j, "barge-in: audio still sent after cancel", f"{barge.talk_over_s} s",
                    barge.talk_over_s <= TALK_OVER_S, f"<= {TALK_OVER_S} s", weight=3,
                    workaround="gate audio client-side after cancel (it is still streamed and likely billed)",
                    evidence=barge.request_ids[:2], note=f"English median {EN['talk_over_s']} s (R1)")
    scorecard.check(j, "next turn after barge-in answered", after.ttfa_ms, after.ttfa_ms is not None,
                    "audio within 10 s", weight=2, blocker=True, evidence=after.request_ids[:1],
                    note=f"English median {EN['after_barge_ms']} ms")
    scorecard.check(j, "Hindi sentence released at the danda (।)", danda, danda_ok,
                    f"first audio <= {BOUNDARY_MS} ms (the rest follows 2.5 s later)", weight=2,
                    workaround=DANDA_FIX if fix else None,
                    note="continuations.md, How buffering works: terminal punctuation is `. ? ! …`")
    brand_says = state.get("brand_says")
    clips = [(f"turn {n}", t.audio_s, spoken(SCRIPT[n].text, brand_says)) for n, t in enumerate(turns)]
    clips += [("after barge-in", after.audio_s, llm_hi.AFTER_BARGE_IN),
              ("danda sentence", boundary_s, f"{llm_hi.BOUNDARY_FIRST}। {llm_hi.BOUNDARY_REST}")]
    caller_rate = [round((audio.duration(w, 16000) or 0) / len(t), 3) for t, w in hindi_callers]
    _check_runaway(scorecard, j, clips, ids + after.request_ids[:1],
                   note=f"stock-voice caller clips {caller_rate} s/char")
    scorecard.check(j, "call stays connected (keepalive, no errors)", f"closed_at={closed_at} errors={len(errors)}",
                    closed_at is None and not errors, "open, no error frames", weight=2, blocker=True,
                    note=f"errors: {errors[:2]}" if errors else "")
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_03_phone_call(state, scorecard, hindi_callers):
    """The same agent on a phone line: caller audio arrives as 8 kHz mu-law, the agent's 8 kHz audio is encoded
    to mu-law and fed to a carrier in 20 ms frames. Runs with what the web call taught (date_format=EU, and '.'
    for '।' if the danda was not a sentence boundary)."""
    j = "phone call (hi)"
    profile = require_profile(state)
    llm = ScriptedLLM()
    fix = state.get("danda_fix", False)
    extra = {"language": "hi", "date_format": "EU"}
    lines = [(n, _phone_line(hindi_callers[n][1])) for n in (0, 2)]

    async def tokens(text: str):
        async for tok in llm.stream(text):
            yield tok.replace("।", ".") if fix else tok

    async def call():
        out = []
        async with live.live(label="e2e-hi-phone-call") as sock:
            agent = AgentSession(sock, profile, sample_rate=phone.RATE, extra=extra)
            for n, clip in lines:
                heard, _ = await asyncio.to_thread(_stt, clip, f"e2e-hi-phone-stt-{n}", "hi")
                start = sock.now()
                turn = await agent.finish(await agent.say(tokens(SCRIPT[n].text), f"qa-hi-phone{n}-{RUN_ID}"))
                arrivals = [(f["t"], f["data"]["audio_bytes"] // 2) for f in sock.chunks_after(turn.first_sent_ms)]
                ulaw = phone.mulaw_encode(_turn_pcm(sock, turn))
                latency = (heard.total_ms or 0) + (turn.first_sent_ms - start) + (turn.ttfa_ms or 0)
                out.append((n, turn, ulaw, phone.carrier_pacing(arrivals), latency, heard.request_id))
                await asyncio.sleep(1.5)
            return out, sock.errors()

    results, errors = asyncio.run(call())
    ids = [t.request_ids[0] for _, t, *_ in results if t.request_ids]
    late = [p["late_frames"] for _, _, _, p, _, _ in results]
    scorecard.check(j, "no late 20 ms frames at carrier pace", late, all(x == 0 for x in late),
                    "0 late frames (60 ms jitter buffer)", weight=3, evidence=ids,
                    note=f"worst late {[p['worst_late_ms'] for _, _, _, p, _, _ in results]} ms")
    framed = [phone.frames(u) for _, _, u, _, _, _ in results]
    well_formed = all(fr and all(len(x) == phone.FRAME_BYTES for x in fr) for fr in framed)
    scorecard.check(j, "audio frames as 160-byte mu-law", well_formed, well_formed, "all frames 160 bytes",
                    evidence=ids)
    lat = [round(x) for *_, x, _ in results]
    scorecard.check(j, "response latency, median", statistics.median(lat), statistics.median(lat) <= RESPONSE_MS,
                    f"<= {RESPONSE_MS} ms", weight=2, evidence=[r[-1] for r in results] + ids[:1],
                    note=f"per turn {lat} ms incl. Pulse hi on 8 kHz mu-law caller audio; '.' for '।': {fix}; "
                         f"English median {EN['phone_ms']} ms")
    trips = _round_trips([(SCRIPT[n], _wav(_ulaw_decode(u), phone.RATE)) for n, _, u, *_ in results],
                         "e2e-hi-phone-rt", state.get("brand_says"))
    _score_round_trips(scorecard, j, trips, None, f"8 kHz mu-law, date_format=EU, '.' for '।': {fix}")
    _check_runaway(scorecard, j, [(f"turn {n}", t.audio_s, spoken(SCRIPT[n].text, state.get("brand_says")))
                                  for n, t, *_ in results], ids)
    scorecard.check(j, "date_format accepted on the socket (no error frames)", len(errors), not errors,
                    "0 error frames", note=f"errors: {errors[:2]}" if errors else "")
    assert_journey(scorecard, j)
