# Write-up

## How the tool works

An admin saves criteria as a numbered version. A reviewer uploads proposals and picks a category. Code reads each PDF and scans it for embedded instructions. AI extracts facts with quotes, and code checks the quotes. Code then applies the mandatory checks, scores, ranks and writes the reason lines. A reviewer checks the result, and a person makes the award. See the [diagram](diagram/process-flow.png).

## Scoring used for the samples

The admin picks a scoring method for each criterion from a short list, so no criterion is hard-coded. Each criterion scores 0 to 100, then the weights apply.

| Criterion | Method |
|---|---|
| Experience | 10 points per qualifying install, capped at 100 |
| Price | Lowest eligible price divided by this price |
| Timeline | Shortest stated schedule divided by this schedule. Missing, or over 16 weeks, scores 0 |
| Warranty | Half panel years against 25, half workmanship years against the best offer |
| Team | 25 points each for lead, crew, safety plan and monitoring plan |

Assumptions, since I did not wait for a reply to questions:

- "Last 5 years" means 2021 onward, so "since 2021" counts. C's "since 2020" needs a dated list. Its reference score uses the stated count.
- A lead described as named, with no name given, earns half of that item (12.5 points).
- The 16-week limit is not a pass/fail check, because the admin did not set it up as one. If it were, D would become ineligible through configuration alone.
- C still counts toward the lowest price and schedule values because it passed the mandatory checks.
- Prices are compared as stated. Only A and B say what their price covers, so a reviewer should confirm this before award.

## 1. AI vs. rules

AI does one job, which is reading unstructured text and pulling out facts with a quote and page number. Proposals word the same thing in different ways, and rules handle that badly.

Everything else is plain code: PDF text reading, the instruction scan, quote checks, mandatory checks, scoring, ranking and logging. Those steps need the same answer every time, and arithmetic should never depend on a model. This also limits manipulation, because the AI has no power over a score.

## 2. Consistency and explainability

Scoring and ranking are code, so the same facts always give the same result. AI output can vary a little between runs, even at temperature 0. The tool therefore stores each extraction by file, prompt and criteria version. Ranking the same proposals twice reuses the stored facts and gives an identical result. A fresh extraction only happens when one of those versions changes.

For every proposal, the reviewer sees each criterion's score, the formula, the quote and the page. Reason lines are built from those same facts, starting with any problem.

## 3. Human in the loop

- The admin sets and approves criteria before use.
- The reviewer handles exceptions: unreadable files, embedded instructions, failed quote checks and failed mandatory checks.
- The reviewer checks the full result and can correct a fact or override an outcome. An override needs a written reason. Corrected facts are rescored by the same code.
- A person makes the award. The tool never does.

The audit log keeps file hashes, criteria, prompt and model versions, the raw AI response, quotes, scores, flags, and each change with who made it, when and why. The original result is never overwritten.

## 4. Changing criteria

Each edit creates a new version, and every score stays tied to the version that produced it. A batch is never ranked across mixed versions. If an admin edits criteria mid-review:

- Existing results stay visible but are marked out of date.
- A weight change only needs the code to rerun, with no AI cost.
- A new or reworded criterion needs extraction for that criterion only.
- The reviewer sees old and new rankings side by side and confirms the change. Past awards keep their original version.

## 5. Risks

| Risk | Guard |
|---|---|
| Wrong extraction | Quotes and pages sit beside each fact. Unclear values go to the reviewer. |
| Made-up facts | Every quote must appear word for word in the proposal. If not, the value counts as not found. |
| Missing information | Extraction returns "not found", the criterion scores 0, and the reason says so. No value is assumed. D is the example. |
| Claims that fall short | Extraction records who holds a licence. B's subcontractor "to be confirmed" fails the check despite B's low price. |
| Manipulation | Proposal text is treated as data. A code scan and the AI both report embedded instructions, and hidden text is checked. The proposal is flagged and unranked until a person decides. |
| False accusation | The tool describes what the text says and recommends action. It cannot prove who wrote it, so a person makes the disqualification call. |
| Bias | Scoring uses facts only, not company name or writing style. The experience cap stops size from dominating. Reviewers can audit overrides for patterns. |
| Cost | One call per proposal, stored results, file size limits and a spending cap per batch. |
| Over-trust | The list is labelled as a recommendation, and the award stays with a person. |

## Sample result

A ranks first (96.1), E second (89.8) and D third (74.4). B is ineligible because the bidder does not hold the licence. C is flagged. It would score 82.9 without the embedded instruction, but that figure is for reference only. The instruction comes first in C's reason because it raises a concern about how the bidder would behave on the project, however good the price.
