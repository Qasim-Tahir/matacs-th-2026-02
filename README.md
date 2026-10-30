# AI proposal triage design

Full name: Qasim Tahir

Reference: MATACS-TH-2026-02

Time actually spent: About 60 to 70 minutes

## Files

- [WRITEUP.md](WRITEUP.md): answers to the five questions, scoring method and assumptions
- [diagram/process-flow.png](diagram/process-flow.png): process flow from upload to ranked output
- [PROMPTS.md](PROMPTS.md): the AI extraction prompt
- [ranking.json](ranking.json): expected ranking of proposals A to E
- [prototype/](prototype/README.md): optional script that runs the flow. A live run on Groq with `openai/gpt-oss-120b` matched `ranking.json` on every rank and status.

## How I used AI tools

I used Claude to work through the brief and draft the diagram, prompt, write-up and prototype, used ChatGPT to critique the design, and reviewed the decisions and result myself. I disagreed with Claude's first draft of the reason for Proposal C, which led with its score without the embedded instruction, and changed it to lead with the manipulation attempt, because a good price from a bidder who games the evaluation is still a warning sign. I also rejected its alternative scoring ideas in favour of min-max scaling for price and timeline, and removed its 10-install experience cap because it hid real differences in experience.
