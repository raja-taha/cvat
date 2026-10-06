# Plan — Annotation Analytics Assessment

**Fork SHA at clone:** `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5`  
**Branch:** `dev-test01`  
**Window:** 8 hours of work. Docker pull / dataset import wait is outside that.

## Intent

Add per-class annotation counts for a CVAT task: read from the database, expose an API, show a graph. Stay inside a new Django app named `test`. Do not open a PR against upstream CVAT.

## Order of work (original budget)

| Block | Hours | What |
| --- | --- | --- |
| A | ~0.5 | This Plan, then Definition of Done and Objectives. No feature code until Plan is committed. |
| B | (clock not counted) | `CVAT_HOST=localhost docker compose up -d`, superuser, COCO val2017 task. Write down image count. Ready when a job shows labelled boxes. |
| C | ~2.0 | Item 1. Django app `cvat.apps.test`. `GET /api/test/tasks/<id>/annotation-counts`. |
| D | ~2.0 | Items 2–4 (floor). Page, graph, empty and failed-request states. |
| E | ~0.75 | Item 5. Login required; no access → 403. |
| F | ~0.75 | Item 6. Speed target, five runs. |
| G | ~0.5 | Item 7. Group by `source`. |
| H | remainder | Evidence. Items 8–10 only if 1–7 exist. |

## What changed after the first commit

- **Server code** is bind-mounted into `cvat_server` (`/opt/cvat/cvat`) so we did not rebuild the server image. Rebuilding the server with `docker-compose.dev.yml` failed once on a truncated FFmpeg download; we left workers on the published image.
- **Page (item 2):** Traefik only sends `/api/` to Django. The floor page is therefore Django HTML at `/api/test/tasks/<id>/analytics`, not a first-cut `cvat-ui` Chart.js route. Later we rebuilt **only** `cvat_ui` so Jobs/Tasks **View analytics** opens that URL instead of the paid `/tasks/:id/jobs/:id/analytics` page.
- **Sample data:** 200 COCO val2017 images per task, not the full 5,000. The full `instances_val2017.json` does not match a 200-frame task (`Could not match item id`). We import a filtered subset. Labels must be the lowercase COCO names (`person` ≠ `Person`).
- **Item 7** landed with the counts query (always `by_source` and `by_kind`), not as a later add-on. The page filters those fields.
- **Create project/task** buttons were collapsed to a single **Submit** (no open/continue). Extra to the brief; not required.

## Already skipping (still)

- **Items 8–9 (WebSocket live graph + reconnect).** The floor, auth, measurement and source grouping work. A live channel has to follow CVAT’s annotation write path, not a private socket. Time left is for evidence, recording and a PR on this fork, not a half-finished websocket.
- **Recording and fork PR** are submission steps, not feature work. They are still outstanding at the time of this update.

## Decision record (item 10)

**Took:** a new Django app `cvat.apps.test` that `COUNT`s `LabeledShape` / `LabeledImage` / `LabeledTrack` grouped by `Label`, behind `TaskPermission` VIEW. The page is HTML under `/api/test/` so Traefik routes it without a UI rebuild for items 1–4.

**Rejected:** (1) counting from the uploaded COCO JSON or ClickHouse events — the brief says read from the database; those sources are not the annotation tables. (2) putting the first graph only in `cvat-ui` — a UI image rebuild is slow and failed when Compose also rebuilt the server.

**Cost of rejecting those:** we had to learn Job → Segment → Task and `Label.name`, and live with a page that is not the React SPA until we later rebuilt `cvat_ui` for the menu link. We also cannot show live updates without item 8.

## What “done enough to submit” means

Items 1–7 working on the 200-image COCO tasks, three docs with evidence, incremental commits. Do not ship 8–9. Then Loom ≤ 5 minutes and a PR **on this fork** (`dev-test01` → `main` of `raja-taha/cvat`).
