"""End-to-end journeys of a branded voice support agent built on the Smallest Models API.

The product (src/smallest_qa/app): a support agent that speaks in a cloned brand voice, answers callers on the
web and by phone, uses a pronunciation dictionary for the brand name, handles barge-in, and can be offboarded.
Each journey records product-level checks in the Scorecard (see app/scorecard.py for scoring and verdicts).

Journeys run in file order and share ONE clone (the API cannot delete clones, so every run leaves one to remove
in the dashboard). Inputs are the owner's own recording only (voice to clone and caller utterances).

Thresholds (the product's budget, not the docs'):
  response latency  caller stops speaking -> first agent audio <= 1500 ms (median); STT is the pre-recorded API
  TTS first audio   first text fragment sent -> first audio chunk <= 400 ms (median)
  no audible gaps   playback started at the first chunk (+150 ms buffer) never runs dry
  barge-in          audio still streamed after cancel <= 0.3 s
  reconnect         network drop -> first audio on the new connection <= 2000 ms
  phone             no late 20 ms mu-law frames with a 60 ms carrier jitter buffer
"""

import asyncio
import statistics
import time

import pytest

from smallest_qa.app import phone
from smallest_qa.app.llm import BRAND, INTERRUPTIBLE, ScriptedLLM
from smallest_qa.app.profile import VoiceProfile, dictionary_ids_valid, prepare_sample, upload_clone, wait_ready
from smallest_qa.app.session import AgentSession
from smallest_qa.config import settings
from smallest_qa.utils import audio, live
from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.utils.retry import with_backoff
from smallest_qa.waves import cloning, pronunciation, stt, tts
from smallest_qa.waves.payloads import DROP, V31_MODEL, tts_body

from .conftest import assert_journey, require_profile

pytestmark = pytest.mark.clone

RESPONSE_MS, TTFA_MS, RECONNECT_MS, TALK_OVER_S = 1500, 400, 2000, 0.3
BRAND_SAYS = "quick zebra vision express"  # long respelling: the dictionary's effect is measurable in seconds
PREVIEWS = {"en": f"Hello, and welcome to {BRAND} support.",
            "hi": "नमस्ते, सपोर्ट में आपका स्वागत है।",
            "es": "Hola, bienvenido al servicio de atención al cliente."}


def _stt(wav: bytes, label: str, language: str = "en"):
    """Caller audio -> text, retried the documented way if Pulse rate-limits (it does at ~1 req/s)."""
    tries = with_backoff(lambda: stt.transcribe(wav, language, label=label), label=f"{label}-retry")
    return tries.final, tries


def _brand_seconds(profile_dicts: list[str], label: str, voice: VoiceProfile) -> tuple[float, str]:
    ex = tts.synthesize(tts_body(text=f"Welcome to {BRAND}.", voice_id=voice.voice_id, model=voice.model,
                                 output_format="wav", pronunciation_dicts=profile_dicts or DROP), label=label)
    return (audio.duration(ex.body, 24000) or 0.0) if ex.status == 200 else 0.0, ex.request_id


# ---------------------------------------------------------------------------------------------------------------
def test_01_onboarding(state, scorecard, sample, tmp_path):
    """Brand uploads its voice from the web app, waits for the clone, previews it in 3 languages, adds the
    brand-name dictionary."""
    j = "onboarding"
    clip = prepare_sample(sample, tmp_path / "brand_voice.wav")
    vid, attempts = upload_clone(clip, name=f"qa-e2e-{RUN_ID}")
    scorecard.check(j, "upload accepted with the browser's MIME label (audio/x-wav)", attempts[0].status,
                    attempts[0].status == 200, "200", workaround="re-label uploads as audio/wav before sending",
                    evidence=[a.request_id for a in attempts])
    scorecard.check(j, "clone created", bool(vid), bool(vid), "voice id returned", weight=3, blocker=True,
                    evidence=[attempts[-1].request_id])
    if not vid:
        assert_journey(scorecard, j)
    state["clone_ids"].append(vid)
    status, waited = wait_ready(vid)
    scorecard.check(j, "clone ready", f"{status} after {waited} s", status == "completed" and waited <= 30,
                    "completed within 30 s", weight=2, blocker=True)
    profile = VoiceProfile(voice_id=vid)
    state["profile"] = profile

    for lang, text in PREVIEWS.items():
        ex = tts.synthesize(tts_body(text=text, voice_id=vid, model=profile.model, language=lang, output_format="wav"),
                            label=f"e2e-preview-{lang}")
        time.sleep(1.2)  # Pulse STT limit
        heard, _ = _stt(ex.body, f"e2e-preview-stt-{lang}", lang) if ex.status == 200 else (None, None)
        sim = stt.similarity(text, stt.text(heard)) if heard else 0.0
        scorecard.check(j, f"preview intelligible in {lang}", sim, ex.status == 200 and sim >= 0.6,
                        ">= 0.6 STT similarity", evidence=[ex.request_id, heard and heard.request_id])

    d = pronunciation.create([{"word": BRAND, "pronunciation": BRAND_SAYS}])
    dict_id = (d.json or {}).get("id") if isinstance(d.json, dict) else None
    plain, rid_plain = _brand_seconds([], "e2e-brand-plain", profile)
    with_dict, rid_dict = _brand_seconds([dict_id] if dict_id else [], "e2e-brand-dict", profile)
    applied = bool(dict_id) and with_dict - plain >= 0.4
    scorecard.check(j, "brand dictionary applied", f"{plain} s -> {with_dict} s", applied, ">= +0.4 s with dictionary",
                    weight=2, evidence=[d.request_id, rid_plain, rid_dict])
    if dict_id:
        profile.dict_ids = [dict_id]
        state["dict_id"] = dict_id
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_02_web_call_with_barge_in(state, scorecard, caller_clips):
    """A caller on the website: three turns (caller speaks -> STT -> scripted LLM -> cloned voice), then the
    caller interrupts a long answer, then asks something else."""
    j = "web call"
    profile = require_profile(state)
    llm = ScriptedLLM()

    async def call():
        turns, latencies, stt_ids = [], [], []
        async with live.live(label="e2e-web-call") as sock:
            agent = AgentSession(sock, profile)
            pinger = asyncio.create_task(agent.keepalive())
            for n, clip in enumerate(caller_clips):
                heard, _ = await asyncio.to_thread(_stt, clip, f"e2e-web-stt-{n}")
                stt_ids.append(heard.request_id)
                start = sock.now()
                turn = await agent.finish(await agent.say(llm.stream(llm.reply(n)), f"qa-web{n}-{RUN_ID}"))
                turns.append(turn)
                if turn.ttfa_ms is not None:
                    latencies.append((heard.total_ms or 0) + (turn.first_sent_ms - start) + turn.ttfa_ms)
                await asyncio.sleep(1.5)
            # barge-in: caller talks over a long answer about 1 s into the audio
            long_turn = await agent.say(llm.stream(INTERRUPTIBLE), f"qa-web-barge-{RUN_ID}")
            first = await sock.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=long_turn.first_sent_ms)
            if first:
                await asyncio.sleep(1.0)
                await agent.interrupt(long_turn)
            long_turn = await agent.finish(long_turn)
            after = await agent.finish(await agent.say(llm.stream("Sure, go ahead. What can I help with?"),
                                                       f"qa-web-after-{RUN_ID}"))
            complete = await sock.wait_for(lambda f: f.get("status") == "complete", timeout=8,
                                           since=after.first_sent_ms)
            last_chunk = max((f["t"] for f in sock.chunks_after(after.first_sent_ms)), default=None)
            pinger.cancel()
            return turns, latencies, stt_ids, long_turn, after, complete, last_chunk, sock.closed_at, sock.errors()

    turns, latencies, stt_ids, barge, after, complete, last_chunk, closed_at, errors = asyncio.run(call())
    ids = [rid for t in turns for rid in t.request_ids[:1]]
    med = statistics.median(latencies) if latencies else None
    scorecard.check(j, "response latency (caller done -> agent audio), median", med and round(med),
                    bool(med) and med <= RESPONSE_MS, f"<= {RESPONSE_MS} ms", weight=3, evidence=stt_ids[:1] + ids[:1],
                    note=f"per turn {[round(x) for x in latencies]} ms incl. pre-recorded STT")
    ttfas = [t.ttfa_ms for t in turns if t.ttfa_ms is not None]
    scorecard.check(j, "TTS first audio, median", statistics.median(ttfas) if ttfas else None,
                    bool(ttfas) and statistics.median(ttfas) <= TTFA_MS, f"<= {TTFA_MS} ms", weight=2, evidence=ids)
    gaps = [t.min_headroom_s for t in turns]
    scorecard.check(j, "no audible gaps in agent speech", gaps, all(g is not None and g >= 0 for g in gaps),
                    "headroom >= 0 every turn", weight=3, evidence=ids)
    scorecard.check(j, "every turn answered", f"{len(ttfas)}/{len(turns)}", len(ttfas) == len(turns),
                    "all turns", weight=3, blocker=True, evidence=ids)
    scorecard.check(j, "barge-in: audio still sent after cancel", f"{barge.talk_over_s} s",
                    barge.talk_over_s <= TALK_OVER_S, f"<= {TALK_OVER_S} s", weight=3,
                    workaround="gate audio client-side after cancel (it is still streamed and likely billed)",
                    evidence=barge.request_ids[:2])
    scorecard.check(j, "next turn after barge-in answered", after.ttfa_ms, after.ttfa_ms is not None,
                    "audio within 10 s", weight=2, blocker=True, evidence=after.request_ids[:1])
    gap_complete = round(complete["t"] - last_chunk) if complete and last_chunk else None
    scorecard.check(j, "end of turn signalled promptly (complete after last audio)", gap_complete,
                    gap_complete is not None and gap_complete <= 1000, "<= 1000 ms",
                    workaround="detect end of speech by audio silence instead of `complete`")
    scorecard.check(j, "call stays connected (keepalive, no errors)", f"closed_at={closed_at} errors={len(errors)}",
                    closed_at is None and not errors, "open, no error frames", weight=2, blocker=True)
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_03_phone_call(state, scorecard, caller_clips):
    """The same agent on a phone line: 8 kHz audio encoded to mu-law and fed to a carrier in 20 ms frames."""
    j = "phone call"
    profile = require_profile(state)
    llm = ScriptedLLM()

    async def call():
        out = []
        async with live.live(label="e2e-phone-call") as sock:
            agent = AgentSession(sock, profile, sample_rate=phone.RATE)
            for n in range(2):
                heard, _ = await asyncio.to_thread(_stt, caller_clips[n], f"e2e-phone-stt-{n}")
                start = sock.now()
                turn = await agent.finish(await agent.say(llm.stream(llm.reply(n)), f"qa-phone{n}-{RUN_ID}"))
                chunks = [f for f in sock.chunks_after(turn.first_sent_ms)]
                pcm = b"".join(bytes(sock.audio.get(rid, b"")) for rid in turn.request_ids)
                ulaw = phone.mulaw_encode(pcm)
                arrivals = [(f["t"], f["data"]["audio_bytes"] // 2) for f in chunks]
                latency = (heard.total_ms or 0) + (turn.first_sent_ms - start) + (turn.ttfa_ms or 0)
                out.append((turn, phone.frames(ulaw), phone.carrier_pacing(arrivals), latency))
                await asyncio.sleep(1.5)
        return out

    results = asyncio.run(call())
    ids = [rid for t, *_ in results for rid in t.request_ids[:1]]
    late = [p["late_frames"] for _, _, p, _ in results]
    scorecard.check(j, "no late 20 ms frames at carrier pace", late, all(x == 0 for x in late),
                    "0 late frames (60 ms jitter buffer)", weight=3, evidence=ids,
                    note=f"worst late {[p['worst_late_ms'] for _, _, p, _ in results]} ms")
    well_formed = all(fr and all(len(x) == phone.FRAME_BYTES for x in fr) for _, fr, _, _ in results)
    scorecard.check(j, "audio frames as 160-byte mu-law", well_formed, well_formed, "all frames 160 bytes",
                    evidence=ids)
    lat = [round(x) for *_, x in results]
    scorecard.check(j, "response latency, median", statistics.median(lat), statistics.median(lat) <= RESPONSE_MS,
                    f"<= {RESPONSE_MS} ms", weight=2, evidence=ids)

    # does the WebSocket honour output_format=ulaw (REST does, undocumented)? compare bytes with 8 kHz PCM
    async def native():
        sizes = {}
        async with live.live(label="e2e-phone-native") as sock:
            for fmt in ("pcm", "ulaw"):
                t = await sock.send({"text": "Your delivery is confirmed.", "voice_id": profile.voice_id,
                                     "model": profile.model, "sample_rate": 8000, "output_format": fmt})
                await sock.wait_for(lambda f: f.get("status") == "complete", timeout=12, since=t)
                sizes[fmt] = sock.audio_bytes_after(t)
        return sizes

    sizes = asyncio.run(native())
    ratio = round(sizes["ulaw"] / sizes["pcm"], 2) if sizes.get("pcm") else None
    scorecard.check(j, "WebSocket delivers mu-law natively", f"ulaw/pcm bytes = {ratio}",
                    ratio is not None and 0.35 <= ratio <= 0.65, "~0.5 (1 byte/sample)",
                    workaround="request 8 kHz PCM and encode G.711 mu-law on our side")
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_04_busy_hour(state, scorecard, caller_clips):
    """Three callers at once (within the brief's cap), two turns each, STT shared through one client."""
    j = "busy hour"
    profile = require_profile(state)
    if settings.max_in_flight < 4:
        pytest.skip("needs 3 sockets + 1 STT request at once: run with QA_MAX_IN_FLIGHT=4")
    llm = ScriptedLLM()
    stt_lock = asyncio.Lock()

    async def caller(k: int):
        turns, stt_429 = [], 0
        await asyncio.sleep(k * 0.6)
        async with live.live(label=f"e2e-busy-{k}") as sock:
            agent = AgentSession(sock, profile)
            for n in range(2):
                async with stt_lock:
                    heard, tries = await asyncio.to_thread(_stt, caller_clips[(k + n) % len(caller_clips)],
                                                           f"e2e-busy-stt-{k}-{n}")
                    stt_429 += tries.statuses.count(429)
                turns.append(await agent.finish(await agent.say(llm.stream(llm.reply(n + k)),
                                                                f"qa-busy{k}-{n}-{RUN_ID}")))
                await asyncio.sleep(1.0)
        return turns, stt_429

    async def hour():
        return await asyncio.gather(*(caller(k) for k in range(3)))

    results = asyncio.run(hour())
    turns = [t for ts, _ in results for t in ts]
    ids = [t.request_ids[0] for t in turns if t.request_ids]
    served = sum(t.ttfa_ms is not None for t in turns)
    scorecard.check(j, "every turn answered (3 concurrent calls)", f"{served}/{len(turns)}", served == len(turns),
                    "all turns", weight=3, blocker=True, evidence=ids)
    ttfas = sorted(t.ttfa_ms for t in turns if t.ttfa_ms is not None)
    p90 = ttfas[int(0.9 * (len(ttfas) - 1))] if ttfas else None
    scorecard.check(j, "TTS first audio under load, p90", p90, p90 is not None and p90 <= 600, "<= 600 ms",
                    weight=2, evidence=ids)
    gaps = [t.min_headroom_s for t in turns]
    scorecard.check(j, "no audible gaps under load", gaps, all(g is not None and g >= 0 for g in gaps),
                    "headroom >= 0", weight=2, evidence=ids)
    stt_429 = sum(x for _, x in results)
    scorecard.check(j, "speech-to-text keeps up (no 429s)", stt_429, stt_429 == 0, "0 rate-limit responses",
                    workaround="serialize STT and back off on 429 (no Retry-After header)")
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_05_network_drop(state, scorecard):
    """The caller's connection drops mid-answer; the agent reconnects and finishes the answer."""
    j = "network drop"
    profile = require_profile(state)
    llm = ScriptedLLM(first_token_ms=0)
    reply = llm.reply(0)

    async def call():
        async with live.live(label="e2e-drop-before") as sock:
            agent = AgentSession(sock, profile)
            turn = await agent.say(llm.stream(reply), f"qa-drop-{RUN_ID}")
            await sock.wait_for(lambda f: f.get("status") == "chunk", timeout=10, since=turn.first_sent_ms)
            await asyncio.sleep(0.8)
            heard_before = sock.audio_bytes_after(turn.first_sent_ms) / 48000
            sock.sock.transport.abort()
            dropped = time.perf_counter()
        async with live.live(label="e2e-drop-after") as sock2:
            agent2 = AgentSession(sock2, profile)
            resumed = await agent2.finish(await agent2.say(llm.stream(reply), f"qa-drop-resume-{RUN_ID}"))
            reconnect_ms = round((time.perf_counter() - dropped) * 1000 - (sock2.now() - resumed.first_sent_ms)
                                 + (resumed.ttfa_ms or 0))
            return heard_before, resumed, reconnect_ms

    heard_before, resumed, reconnect_ms = asyncio.run(call())
    scorecard.check(j, "drop -> first audio on the new connection", reconnect_ms,
                    resumed.ttfa_ms is not None and reconnect_ms <= RECONNECT_MS, f"<= {RECONNECT_MS} ms",
                    weight=3, blocker=True, evidence=resumed.request_ids[:1],
                    note=f"{round(heard_before, 2)} s heard before the drop")
    scorecard.check(j, "answer completed after reconnect", f"{resumed.audio_s} s", resumed.audio_s > 4, "> 4 s audio",
                    weight=2, evidence=resumed.request_ids[:1])
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_06_dictionary_change(state, scorecard):
    """Marketing changes how the brand is said mid-day; later the dictionary is removed. Calls must follow."""
    j = "dictionary change"
    profile = require_profile(state)
    dict_id = state.get("dict_id")
    if not dict_id:
        pytest.skip("no dictionary from onboarding")
    before, rid_before = _brand_seconds([dict_id], "e2e-dict-before", profile)
    up = pronunciation.update(dict_id, [{"word": BRAND, "pronunciation": "kwiz"}])
    after, rid_after = _brand_seconds([dict_id], "e2e-dict-after", profile)
    scorecard.check(j, "updated pronunciation used on the next call", f"{before} s -> {after} s",
                    up.status == 200 and before - after >= 0.4, ">= 0.4 s shorter after the update", weight=2,
                    evidence=[up.request_id, rid_before, rid_after])
    gone = pronunciation.delete(dict_id)
    stale = tts.synthesize(tts_body(text=f"Welcome to {BRAND}.", voice_id=profile.voice_id, model=profile.model,
                                    pronunciation_dicts=[dict_id]), label="e2e-dict-stale")
    scorecard.check(j, "call with a deleted dictionary is rejected", stale.status, 400 <= stale.status < 500,
                    "4xx", weight=2, evidence=[gone.request_id, stale.request_id],
                    workaround="validate dictionary ids against GET /pronunciation-dicts before each call")
    guard = dictionary_ids_valid([dict_id])
    scorecard.check(j, "product guard drops the stale id", guard, guard == [], "[]")
    profile.dict_ids = guard
    assert_journey(scorecard, j)


# ---------------------------------------------------------------------------------------------------------------
def test_07_offboarding(state, scorecard):
    """The voice owner leaves: their cloned voice must be deleted and unusable (a privacy requirement)."""
    j = "offboarding"
    profile = require_profile(state)
    deleted = cloning.delete(profile.voice_id)
    listed = cloning.find(cloning.list_clones(), profile.voice_id)
    still = tts.synthesize(tts_body(text="This voice should be gone.", voice_id=profile.voice_id, model=profile.model),
                           label="e2e-offboard-check")
    manual = "delete by hand in the dashboard (no API, no audit trail; does not scale)"
    scorecard.check(j, "delete the cloned voice via the API", deleted.status, deleted.status in (200, 204),
                    "200/204", weight=3, blocker=True, workaround=manual, evidence=[deleted.request_id])
    scorecard.check(j, "deleted voice gone from the list and unusable",
                    f"listed={bool(listed)} tts={still.status}", not listed and 400 <= still.status < 500,
                    "not listed, TTS 4xx", weight=3, blocker=True, workaround=manual, evidence=[still.request_id])
    other = tts.synthesize(tts_body(text="Old pool check.", voice_id=profile.voice_id, model=V31_MODEL),
                           label="e2e-offboard-v31")
    scorecard.check(j, "clone on the retiring model (info)", other.status, True, "informational",
                    weight=0, evidence=[other.request_id], note="the Pro clone also speaks on lightning_v3.1 (C5)")
    print(f"\nclones to delete in the dashboard: {state['clone_ids']}")
    assert_journey(scorecard, j)
