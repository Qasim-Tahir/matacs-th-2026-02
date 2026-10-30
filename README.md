# AI proposal triage design

Full name: Qasim Tahir

Reference: MATACS-TH-2026-02

Time actually spent: About 60 to 70 minutes

## Files

- [WRITEUP.md](WRITEUP.md): answers to the five questions, scoring method and assumptions
- [diagram/process-flow.png](diagram/process-flow.png): process flow from upload to ranked output
- [PROMPTS.md](PROMPTS.md): the AI extraction prompt
- [ranking.json](ranking.json): expected ranking of proposals A to E
- [prototype/](prototype/README.md): optional script that runs the flow. I tested the checks, scoring and ranking on the samples using hand-written extraction files. It reproduces `ranking.json`. The live AI call has not been run, because I had no API key available.

## How I used AI tools

I used Claude to walk through the brief, compare design options, and draft the diagram, prompt and write-up, then I reviewed the decisions and the result. I disagreed with its first draft of the reason for Proposal C, which led with what C would score without the embedded instruction. I changed it to lead with the manipulation attempt and its integrity risk, because a good price from a bidder who tries to game the evaluation is still a warning sign for the project.
