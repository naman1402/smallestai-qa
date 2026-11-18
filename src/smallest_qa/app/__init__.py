"""A small prototype of a product built on the Smallest Models API: a branded voice support agent.

The agent speaks in a cloned voice, answers callers on the web and by phone (8 kHz mu-law), handles barge-in,
uses a pronunciation dictionary for brand names, and can be offboarded (voice deleted). The e2e suite in
tests/e2e drives customer journeys through it and fills a go/no-go Scorecard.

llm.py        scripted LLM that streams replies token by token (repeatable runs, no third-party calls)
profile.py    VoiceProfile: onboarding (clone, previews, dictionary) and offboarding
session.py    AgentSession: one call over the TTS WebSocket (turns, barge-in, metrics)
phone.py      mu-law encoding, 20 ms framing and a carrier pacing simulation
scorecard.py  weighted checks per journey -> GO / GO WITH WORKAROUNDS / NO-GO
"""
