"""One request, three transports: REST, SSE and WebSocket should give the same audio.

docs/reference/smallest-docs-2026-11-18/models__text-to-speech__choosing-a-transport.md presents them as
interchangeable ways to get the same synthesis, so a customer who prototypes on REST and ships on
WebSocket expects the same length and format. Durations are compared, not waveforms (generation varies).
"""

import asyncio

from smallest_qa.utils import audio
from smallest_qa.waves import tts
from smallest_qa.waves.payloads import tts_body, ws_payload

TEXT = "Your appointment is confirmed for Tuesday at three thirty in the afternoon."
RATE = 24000


def test_same_text_gives_same_audio_on_every_transport():
    rest = tts.synthesize(tts_body(text=TEXT, output_format="pcm", sample_rate=RATE), label="parity-rest")
    sse = tts.synthesize_sse(tts_body(text=TEXT, output_format="pcm", sample_rate=RATE), label="parity-sse")
    sock = asyncio.run(tts.synthesize_ws(ws_payload(text=TEXT, sample_rate=RATE), label="parity-ws"))
    assert rest.status == 200 and sse.status == 200 and sock.audio, f"{rest} | sse={sse.error_body} | ws={sock.frames}"

    got = {"rest": rest.body, "sse": sse.audio, "ws": sock.audio}
    problems = [f"{k} returned a {audio.sniff(v)} header for pcm" for k, v in got.items() if audio.sniff(v)]
    seconds = {k: audio.pcm_duration(len(v), RATE) for k, v in got.items()}
    if max(seconds.values()) > min(seconds.values()) * 1.2:
        problems.append(f"durations differ by more than 20%: {seconds}")
    ids = {"rest": rest.request_id, "sse": sse.request_id, "ws": sock.request_ids[:1]}
    assert not problems, f"{problems} | request ids {ids}"
