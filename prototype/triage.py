#!/usr/bin/env python3
"""Run the proposal triage flow. AI extracts facts. Plain code does everything else."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("TRIAGE_MODEL", "qwen/qwen3.8-27b")
SCAN_PATTERNS = [
    r"automated review", r"rank (it|this)", r"full marks", r"pre-approved",
    r"ignore (all|any|previous)", r"(system|assistant) prompt",
]
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15}


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def numbers(text):
    """Return (position, value) for every number in the text, written as digits or a word."""
    found = [(m.start(), float(m.group().replace(",", ""))) for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text)]
    found += [(m.start(), float(WORDS[m.group().lower()]))
              for m in re.finditer(r"\b(" + "|".join(WORDS) + r")\b", text, re.I)]
    return sorted(found)


def first_number(value):
    found = numbers(str(value)) if value is not None else []
    return found[0][1] if found else None


def load_prompts():
    blocks = re.findall(r"```text\n(.*?)```", (ROOT / "PROMPTS.md").read_text(), re.S)
    return blocks[0].strip(), blocks[1].strip()


def extract_with_ai(text, config):
    from groq import Groq
    system, user = load_prompts()
    criteria = [{k: v for k, v in c.items() if k in ("id", "looking_for", "items")} for c in config["criteria"]]
    user = (user.replace("{category_name}", config["category"])
            .replace("{project_details}", config["project_details"])
            .replace("{criteria_json}", json.dumps(criteria, indent=2))
            .replace("{proposal_text}", text))
    response = Groq().chat.completions.create(
        model=MODEL, temperature=0, max_completion_tokens=8000,
        response_format={"type": "json_object"}, reasoning_effort="default", reasoning_format="hidden",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"Extraction stopped early: {choice.finish_reason}")
    answer = choice.message.content
    return json.loads(answer[answer.index("{"):answer.rindex("}") + 1])


def scan(text):
    return [p for p in SCAN_PATTERNS if re.search(p, squash(text), re.I)]


def check_entry(entry, name, text, labels, notes):
    """Treat a missing quote as not found. Check the value appears in its quote beside its label."""
    if entry.get("status") == "not_found":
        return
    quote = squash(entry.get("quote"))
    if not quote or quote.lower() not in text.lower():
        notes.append(f"{name}: quote not found in the proposal")
        entry["status"], entry["value"] = "not_found", None
        return
    value = first_number(entry.get("value"))
    if value is None:
        return
    in_quote = numbers(quote)
    if value not in [n for _, n in in_quote]:
        notes.append(f"{name}: value does not appear in its quote")
        entry["status"], entry["value"] = "not_found", None
        return
    if not labels:
        return
    clauses = [c for c in re.split(r",| and ", quote.lower()) if any(l in c for l in labels)]
    if not clauses:
        notes.append(f"{name}: quote does not mention the expected label")
    elif not any(value in [n for _, n in numbers(c)] for c in clauses):
        notes.append(f"{name}: value is not in the same clause as its label")


def validate(extraction, config, text):
    """Index the extraction by criterion and return it with any review notes."""
    notes, facts = [], {c["criterion_id"]: c for c in extraction["criteria"]}
    for criterion in config["criteria"]:
        cid = criterion["id"]
        fact = facts.setdefault(cid, {"criterion_id": cid, "status": "not_found", "value": None, "items": []})
        if criterion.get("items"):
            items = {i["item_id"]: i for i in fact.get("items", [])}
            for item in criterion["items"]:
                entry = items.setdefault(item["id"], {"item_id": item["id"], "status": "not_found", "value": None})
                check_entry(entry, f"{cid}.{item['id']}", text, item.get("labels", []), notes)
            fact["items"] = list(items.values())
        else:
            check_entry(fact, cid, text, [], notes)
    return facts, notes


def fails_mandatory(criterion, fact):
    if criterion["rule"] == "held_by_bidder":
        return fact["status"] != "found" or fact.get("held_by") != "bidder"
    return any(i["status"] != "found" for i in fact["items"])


def item_value(fact, item_id):
    return next(first_number(i.get("value")) for i in fact["items"] if i["item_id"] == item_id)


def score_criterion(criterion, fact, pool):
    """Return 0 to 100. Pool holds every proposal that passed the mandatory checks."""
    method, cid = criterion["method"], criterion["id"]
    if method == "checklist":
        credit = {"found": 1, "ambiguous": 0.5, "not_found": 0}
        return 100 * sum(credit[i["status"]] for i in fact["items"]) / len(fact["items"])
    if method == "warranty":
        best = max(item_value(p[cid], "workmanship") or 0 for p in pool)
        panel = item_value(fact, "panel") or 0
        work = item_value(fact, "workmanship") or 0
        return 50 * min(panel / criterion["panel_years"], 1) + 50 * (work / best if best else 0)
    value = first_number(fact.get("value")) if fact["status"] != "not_found" else None
    if value is None:
        return 0
    values = [v for v in (first_number(p[cid].get("value")) for p in pool) if v is not None]
    if method == "share_of_best":
        return 100 * value / max(values)
    limit, best = criterion["limit"], min(values)
    if value > limit:
        return 0
    return 100 if limit == best else 100 * (limit - value) / (limit - best)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", default=str(ROOT / "samples"), help="folder of A.txt to E.txt")
    parser.add_argument("--criteria", default=str(ROOT / "prototype" / "criteria.json"))
    parser.add_argument("--offline", action="store_true", help="use saved extractions, make no AI calls")
    args = parser.parse_args()

    samples, config = Path(args.samples), json.loads(Path(args.criteria).read_text())
    saved = samples / "extractions"
    saved.mkdir(exist_ok=True)
    proposals = {}
    for path in sorted(samples.glob("*.txt")):
        text = path.read_text()
        stored = saved / f"{path.stem}.json"
        if stored.exists():
            extraction = json.loads(stored.read_text())
        elif args.offline:
            raise SystemExit(f"No saved extraction for {path.stem}")
        else:
            extraction = extract_with_ai(text, config)
            stored.write_text(json.dumps(extraction, indent=2))
        facts, notes = validate(extraction, config, squash(text))
        proposals[path.stem] = dict(
            facts=facts, notes=notes, scan=scan(text),
            embedded=extraction.get("embedded_instructions", []),
            hash=hashlib.sha256(text.encode()).hexdigest(), failed=[])

    mandatory = [c for c in config["criteria"] if c["type"] == "mandatory"]
    weighted = [c for c in config["criteria"] if c["type"] == "weighted"]
    for p in proposals.values():
        p["failed"] = [c["id"] for c in mandatory if fails_mandatory(c, p["facts"][c["id"]])]
    pool = [p["facts"] for p in proposals.values() if not p["failed"]]
    for p in proposals.values():
        if not p["failed"]:
            p["scores"] = {c["id"]: round(score_criterion(c, p["facts"][c["id"]], pool), 1) for c in weighted}
            p["total"] = round(sum(score_criterion(c, p["facts"][c["id"]], pool) * c["weight"] / 100 for c in weighted), 1)

    results = []
    for letter, p in proposals.items():
        if p["failed"]:
            results.append(dict(proposal=letter, rank=None, status="ineligible", score=None,
                                reason=f"Failed mandatory check: {', '.join(p['failed'])}."))
        elif p["scan"] or p["embedded"] or p["notes"]:
            issue = "Embedded instruction found. Needs a person's decision." if p["scan"] or p["embedded"] \
                else "Fact checks failed: " + "; ".join(p["notes"]) + "."
            results.append(dict(proposal=letter, rank=None, status="flagged", score=None,
                                reason=f"{issue} For reference only: scores {p['total']}/100."))
        else:
            missing = [c["id"] for c in weighted if c["id"] != "team" and p["scores"][c["id"]] == 0]
            reason = f"No evidence for {', '.join(missing)}, which scores 0. " if missing else ""
            results.append(dict(proposal=letter, rank=None, status="ranked", score=p["total"],
                                reason=reason + f"Criterion scores: {p['scores']}."))
    ranked = sorted((r for r in results if r["status"] == "ranked"), key=lambda r: -r["score"])
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank
    results.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0, r["status"] != "flagged"))

    audit = dict(model=MODEL, criteria_version=config["version"],
                 prompt_hash=hashlib.sha256("".join(load_prompts()).encode()).hexdigest(),
                 proposals={k: {x: p.get(x) for x in ("hash", "scan", "embedded", "notes", "failed", "scores", "total")}
                            for k, p in proposals.items()})
    (samples / "audit.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
