# Smallest AI software engineer take-home

Received 2026-11-17. The brief below is authoritative over every plan in this repo. Three calendar days were available; the brief's work-hour limits still apply.

## Brief (as supplied)

Your brief
Assess the engineering quality of Smallest's products the way a customer's engineer would, then write a QA report. Pick one area and go deep. Judge the engineering, not the ML models: not whether a voice sounds natural, but whether the product does what its docs say, fails clearly and recovers.

APIs
Text-to-speech and speech-to-text over WebSocket and REST, against the docs: error semantics, limits, streaming.
Atoms product
Building an agent, call quality, turn-taking, and what a customer can see about their calls.
Developer experience
Docs accuracy, SDKs, time to the first working call.
Reliability
Reconnects, timeouts, a few requests at once.
Set up
Sign up at app.smallest.ai with <the email you applied with>. We look at usage on that account only.
New accounts get $10 of credit. When it is nearly used up you can ask for one extra $10 on this page.

Rules
No load or stress testing: at most about five requests at once.
No security scanning or penetration testing.
Only your own account and your own data.
A security problem goes only in the report's private security field, never in a finding or on a call. Only the person who owns security reads it.
Two or three focused hours is enough; stop after 24 hours of work in total. We score the quality of your evidence, not the number of findings.
Redact keys and tokens in what you paste: sk_... is enough.
Watch out
Renting a phone number bills $10 on the 1st of each month and can wipe your balance. You don't need one: call your agent from the browser.
The workflow editor is blocked on the free plan. Build your agent with the single-prompt editor.
The report
Scope and why, your method, your findings, what is done well, your top three fixes with why, and the time you spent. Each finding: a title, what you expected and what you observed, the evidence (commands, requests, request IDs, times with your time zone, numbers from several runs), what a customer would see against an SLO, and a severity.
