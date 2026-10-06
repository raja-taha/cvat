# Definition of Done

Written before feature code. Ticked with evidence. A tick with no evidence is untreated.

## Floor (items 1–4)

- [x] Endpoint returns per-class counts from the database for the COCO sample task. Evidence: `GET /api/test/tasks/1/annotation-counts` as admin → `total` 1468, 77 classes, top `person` 434. SQL: `COUNT(*)` on `engine_labeledshape` for task 1, `person`, `parent_id IS NULL` = 434.
- [x] A page in the running stack calls that endpoint. Evidence: `GET /api/test/tasks/1/analytics` (and task 4: `http://localhost:8080/api/test/tasks/4/analytics`). Jobs/Tasks **View analytics** points here after the `cvat_ui` rebuild (`cvat-ui` actions menus + redirect from `/tasks/:tid/.../analytics`).
- [x] Counts are shown as a graph. Evidence: Chart.js bar/doughnut on that page (`docs` not a screenshot file; live URL above).
- [x] Empty case: no matching rows shows “No annotations on this task yet.” / “No annotations match these filters.”, chart hidden. Evidence: `cvat/apps/test/templates/test/analytics.html` (`emptyEl`).
- [x] Failed request: non-OK fetch shows “Could not load counts (status).” Evidence: same template (`showError`). Observed live as **406** when `Accept: application/json` was rejected; after adding `JSONRenderer` / CVAT Accept header, the same path returns 200.

## Auth (item 5)

- [x] No login refused. Evidence: unauthenticated `GET /api/test/tasks/1/annotation-counts` → **401** `{"detail":"Authentication credentials were not provided."}`
- [x] Logged-in user without access refused. Evidence: user `norights` (id 3, not owner/assignee) → **403** `{"detail":"You do not have permission to perform this action."}`

## Objective (item 6)

- [x] MO-1 measured five times. Evidence: raw `curl` `%{time_total}` in `docs/Objectives.md`.
- [x] Median and spread reported. Target **met**: median 68.0 ms (min 62.7, max 70.8) vs 200 ms.

## Extra grouping (item 7)

- [x] Split by annotation `source` (and kind). Evidence: task 1 `person` payload `by_source: {"file": 434}`, `by_kind: {"shape": 434}`. Page filters All / file / manual and Shapes / Tags / Tracks. Chose **source** because COCO import writes `file` and later draws are `manual` — a split you can check after import.

## Live graph (items 8–9)

- [x] Graph updates when annotations change (no full page reload). Evidence: `WS /api/test/tasks/1/ws` with admin session → first frame `{"type":"connected"}`. After `publish_task_changed(1)` (and the same publish from `dataset_manager.task` wrappers), the socket receives `{"type":"annotations_changed","task_id":1}`; the page `loadCounts()` on that message.
- [x] Client reconnects after a drop. Evidence: `analytics.html` `connectLive()` — onclose waits then `open()` again, delay 1s then doubles up to 15s; `visibilitychange` to visible also reopens if the socket is not OPEN. Live badge: connecting / connected / reconnecting.

## Not started / not finished

- **Loom** (≤ 5 min, K1–K4): not recorded yet.
- **PR** `dev-test01` → `main` on fork `raja-taha/cvat` only: not opened yet.

## Process (automatic-reject checks)

- [x] Branch `dev-test01`. First commit `2159dac7b` is Plan only.
- [x] Stepwise commits (app → page → filters → Accept 406 → menus). Messages say what/why.
- [x] Three documents under `docs/`.
- [x] Clone SHA `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5`.
- [x] Sample image count: **200** (Objectives).
- [ ] PR against this fork only — outstanding.
- [ ] Loom — outstanding.

## Stop rule

Floor plus 5–9 and item 10 (decision record in Plan) are done. Remaining work is recording and the fork PR.
