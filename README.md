# Smallest AI Models API: engineering QA

A customer engineer's QA of Smallest's **Models API**: Lightning text-to-speech over REST, SSE and WebSocket,
plus instant voice cloning. It also includes a working prototype of a voice support agent, used to see what the
API's behaviour means for a real product.

**Result:** GO WITH WORKAROUNDS. That means 7 findings that reproduced every run, 2 of them High:

- barge-in can't stop a reply that's already released;
- voice clones can't be deleted through the API.

→ **[QA_REPORT.md](QA_REPORT.md)**

## Read more

| | |
|---|---|
| [QA_REPORT.md](QA_REPORT.md) | Verdict, findings, top 3 fixes |
| [evidence/README.md](evidence/README.md) | Index and summary of the evidence: notes, request ids, raw logs |
| [docs/method.md](docs/method.md) | How it was tested: stages, prototype, scoring, SLOs |
| [docs/runs.md](docs/runs.md) | Every run, with its time, run id and result |
| [AGENTS.md](AGENTS.md) | For coding agents: rules, cost and safety, repo map |

## Run it

```bash
make setup                 # .venv + .env (put SMALLEST_API_KEY in .env)
make test                  # offline harness checks; no key, no network
.venv/bin/pytest tests/tts -v                              # a live suite: spends credit
QA_MAX_IN_FLIGHT=4 .venv/bin/pytest tests/e2e -v -s        # e2e prototype: creates 1 voice clone
```

Read the cost table in [AGENTS.md](AGENTS.md#before-you-run-anything-cost-and-safety) before running any live
suite. Clones can't be deleted through the API, so each one has to be deleted in the dashboard.

Requirements: Python 3.11+ and `ffmpeg`. The cloning and e2e suites also need your own 10–15 s voice recording
at `samples/my_voice.wav`.
