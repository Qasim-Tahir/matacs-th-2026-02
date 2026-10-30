# Prototype

`triage.py` runs the flow from the design. The AI prompt comes straight from `PROMPTS.md`, and the criteria come from `criteria.json`. Plain code does the checks, scoring and ranking.

The brief must not be copied into this repository, so the sample text is not included. Put each proposal in `samples/A.txt` to `samples/E.txt` at the repository root. That folder is ignored by git.

## Model

The default is `openai/gpt-oss-120b` on Groq with `temperature=0`. Set `TRIAGE_MODEL` to use another Groq model. The script retries rate-limited calls and pauses between proposals.

## Run with AI

Copy `prototype/.env.example` to `prototype/.env` and add your key. That file is ignored by git.

```bash
python3 -m venv .venv
.venv/bin/pip install -r prototype/requirements.txt
.venv/bin/python prototype/triage.py
```

Each extraction is saved in `samples/extractions/`, and later runs reuse it. Every run writes `samples/audit.json`.

## Run without AI

With extractions already saved, this makes no AI calls:

```bash
.venv/bin/python prototype/triage.py --offline
```
