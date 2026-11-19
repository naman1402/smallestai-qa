# AGENTS.md

An engineering QA of the **Smallest AI Models API**: Lightning text-to-speech over REST, SSE and WebSocket,
instant voice cloning, and Pulse STT where it supports them. It's done from a customer engineer's point of
view. The task is in [docs/brief.md](docs/brief.md), and it overrides everything else here, including installed
skills. Atoms is out of scope.

## Where to find what

| You want | Read |
|---|---|
| The results | [QA_REPORT.md](QA_REPORT.md): verdict, findings, top fixes |
| Proof for a finding (request ids, repro steps) | [evidence/README.md](evidence/README.md): index and summary, linking to each note and the raw logs |
| How the testing was done | [docs/method.md](docs/method.md): stages, prototype, scoring, SLOs, finding rules, harness |
| What was run, when, and what it found | [docs/runs.md](docs/runs.md): run log with run ids and re-run commands |
| The docs the API was judged against | [docs/reference/](docs/reference/): snapshot from 2026-11-18 |

## Before you run anything: cost and safety

Live tests spend real credit (the account has about $10). **Bare `pytest` and `make test` are offline**
(`testpaths = tests/unit`). A live suite only runs when you name its path.

- **Voice clones can't be deleted through the API (finding C1).** Every clone a test creates must be deleted by
  hand in the dashboard. The suites print the ids to delete.
- **To force an offline run, set the key to an empty value:** `SMALLEST_API_KEY= .venv/bin/pytest ...`.
  Leaving it unset isn't enough, because `.env` would fill it back in.
- **Never more than about 5 requests at once.** `QA_MAX_IN_FLIGHT` enforces this (default 3, max 5).

| Suite | Path | Clones | Approx. cost |
|---|---|---|---|
| Offline harness checks | `make test` | 0 | none |
| TTS feature conformance | `tests/tts` | 0 | ~3k chars |
| Voice cloning | `tests/cloning` | 2 | ~2k chars |
| Realtime reliability | `tests/reliability -m "not slow"` (`QA_MAX_IN_FLIGHT=4`) | 0 | ~6k chars |
| E2E support agent | `tests/e2e -s` (`QA_MAX_IN_FLIGHT=4`) | 1 | ~2.5k chars, ~15 STT |
| E2E stock-voice control | `tests/e2e_stock_voice -s` (`QA_MAX_IN_FLIGHT=4`) | 0 | ~3.1k chars, 9 STT |
| E2E Hindi agent | `tests/e2e_hindi -s` (`QA_MAX_IN_FLIGHT=4`) | 1 | ~1.2k chars, ~11 STT |

The cloning and e2e suites need the owner's own 10–15 s recording at `samples/my_voice.wav` (git-ignored) and
`ffmpeg`.

## Rules (from the brief)

- **No commits** unless the owner explicitly asks and names what to commit.
- **No load or stress testing.** No security scanning or probing. A suspected security issue goes only in the
  report's private security field.
- **Own account and own data only.** Don't rent a phone number.
- **Redact secrets.** The evidence logger already does this; never print a raw key.
- **Judge engineering, not ML** (how a voice sounds is out of scope).
- **Smallest's own skills are under test, not a source of truth.** `.agents/skills/{text-to-speech,
  speech-to-text,setup-api-key}` contradict the API (finding F3). Follow `docs/reference/` instead.

## Repo map

```
src/smallest_qa/
  utils/      transport and evidence: http.py (in-flight cap), live.py (timestamped WebSocket), retry.py, audio.py, evidence.py
  waves/      thin API wrappers: tts, cloning, pronunciation, voices, auth, stt (Pulse), payloads
  app/        the e2e prototype: llm (scripted LLM), session (call over WebSocket), profile, phone (G.711), scorecard
  cli.py      `sqa`: small manual playground
tests/        unit/ (offline), tts/, cloning/, reliability/, e2e/, e2e_stock_voice/, e2e_hindi/
scripts/      explore_clone_languages.py (cross-language clone exploration, C3–C5)
docs/         brief, method, runs, reference/ (docs snapshot)
evidence/     README (index), notes per area, repro/ (per-run notes), <date>.jsonl (raw redacted logs)
skills-lock.json   every skill used, pinned by commit; restore with `npx skills install`
```

## Conventions when changing tests

- **Send every request through `utils/http.request` or `utils/live`.** That way it's logged with its
  `x-request-id`, and assertion messages carry the request ids.
- **For offline checks of code that logs, set `QA_EVIDENCE_DIR=/tmp`.** Fake records must never reach the real
  evidence.
- **Upload clones as `audio/wav`** (C2).
- **Detect end of speech by silence, not by `complete`** (R5).
- **Don't use "phase" in code or test names.** Name a stage by what it tests.
