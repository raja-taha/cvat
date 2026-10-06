# Definition of Done

Written before feature code. Tick with evidence at the end (number, command, URL, or commit SHA). A tick with no evidence is untreated.

## Floor (must work before anything else is claimed)

- [ ] Endpoint returns per-class counts from the database for the COCO sample task. Evidence: request URL, task id, JSON body, and a SQL or admin cross-check of one class.
- [ ] A page in the running stack calls that endpoint. Evidence: URL opened in the browser.
- [ ] Counts are shown as a graph. Evidence: screenshot path or Loom timestamp.
- [ ] Empty case: task with no annotations (or all-zero classes) renders a clear empty state, not a broken chart. Evidence: how it was produced and what the page showed.
- [ ] Failed request: page shows an error state when the API fails (stop the server, or call a missing task, or force a 500). Evidence: what was broken and what the page showed.

## Auth (item 5, after floor)

- [ ] Request with no login is refused. Evidence: status code and body.
- [ ] Logged-in user without access to that task is refused. Evidence: second user, status code.

## Objective (item 6)

- [ ] MO-1 measured five times on this machine. Evidence: raw output pasted in `docs/Objectives.md`.
- [ ] Median and spread reported. Target met, or missed with the reason written down.

## Extra grouping (item 7)

- [ ] Counts can be split (or filtered) by annotation `source`. Evidence: same task, query param, JSON.

## Not started / not finished

- [ ] List every item from the brief that this submission does not include, and why (time, dependency, or risk).

## Process (automatic-reject checks)

- [ ] Work is on `dev-test01`. First commit is the Plan, not finished code.
- [ ] Commits are stepwise; messages say what changed and why.
- [ ] Three documents exist under `docs/`: Plan, Objectives, Definition of Done.
- [ ] Clone SHA recorded: `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5`.
- [ ] Sample task image count written down in Objectives.
- [ ] PR is against this fork only, not `cvat-ai/cvat`.
- [ ] Loom ≤ 5 minutes, feature live, one request followed through, K1–K4 answered without notes.

## Stop rule

If the floor is not solid, stop. Do not claim items 5–10. Submit with this list honest.
