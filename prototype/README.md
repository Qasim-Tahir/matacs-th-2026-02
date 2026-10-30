# Prototype

`triage.py` runs the flow from the design. The AI prompt comes straight from `PROMPTS.md`, and the criteria come from `criteria.json`. Plain code does the checks, scoring and ranking.

The brief must not be copied into this repository, so the sample text is not included. Put each proposal in `samples/A.txt` to `samples/E.txt` at the repository root. That folder is ignored by git.

## Model

The default is Qwen on Groq (`qwen/qwen3.8-27b`) with `temperature=0`. Set `TRIAGE_MODEL` to use another Groq model.

## Run with AI

```bash
pip install -r prototype/requirements.txt
export GROQ_API_KEY=your-key-here
python3 prototype/triage.py
```

Each extraction is saved in `samples/extractions/`, and later runs reuse it. Every run writes `samples/audit.json`.

## Run without AI

With extractions already saved, this makes no AI calls:

```bash
python3 prototype/triage.py --offline
```
