# Plan — Annotation Analytics Assessment

**Fork SHA at clone:** `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5`  
**Branch:** `dev-test01`  
**Window:** 8 hours of work. Docker pull / dataset import wait is outside that.

## Intent

Add per-class annotation counts for a CVAT task: read from the database, expose an API, show a graph. Stay inside a new Django app named `test`. Do not open a PR against upstream CVAT.

## Order of work (and time budget)

| Block | Hours | What |
| --- | --- | --- |
| A | ~0.5 | This Plan, then Definition of Done and Objectives. No feature code until Plan is committed. |
| B | (clock not counted) | `CVAT_HOST=localhost docker compose up -d`, superuser, COCO val2017 task. Write down image count. Ready when a job shows labelled boxes. |
| C | ~2.0 | Item 1. Django app `cvat.apps.test`. `GET /api/test/tasks/<id>/annotation-counts`. Count from DB (`LabeledShape` / `LabeledImage` / `LabeledTrack` → `Job` → `Segment` → `Task`, grouped by `Label.name`). Wire into `INSTALLED_APPS` and `cvat/urls.py` the same way `quality_control` is. |
| D | ~2.0 | Items 2–4 (floor). A page that calls the API, bar chart (Chart.js already in `cvat-ui`), empty state, failed-request state. |
| E | ~0.75 | Item 5. Reuse CVAT login and `TaskPermission` view scope. Unauthenticated → 401. No task access → 403. Demonstrate both. |
| F | ~0.75 | Item 6. One speed target, five runs, median + spread, raw output in Objectives. |
| G | ~0.5 | Item 7. Extra grouping: count by `source` (`file` vs `manual` vs others). COCO import sets `source=file`; later draws are `manual`. That is a real operational split, not a fake filter. |
| H | remainder | Evidence in Definition of Done. If time remains, items 8–10. |

## Already decided to skip unless C–D are done and time remains

- **Items 8–9 (WebSocket live graph + reconnect).** CVAT annotation writes go through existing job APIs; a correct live channel needs their event path, not a side websocket. Starting that before the floor works is an automatic waste of the assessment.
- **Item 10** only if 1–7 exist; then close this Plan with the decision record.

## How the published images will see our code

`docker compose up -d` runs `cvat/server:dev` and `cvat/ui:dev`. Those images do not contain this branch.

- **Server:** after the `test` app exists, rebuild `cvat_server` with `docker-compose.yml` + `docker-compose.dev.yml`, or copy the app into the container and restart. Prefer rebuild of **server only** so workers keep running.
- **UI:** Traefik sends only `/api/`, `/static/`, `/admin`, `/django-rq` to Django. A “page in the web interface” therefore has to live in `cvat-ui`, **or** be served under `/api/test/...` as HTML. First choice: a Django-served HTML page under `/api/test/` so items 2–4 do not depend on rebuilding the UI image. If that lands quickly, add a `cvat-ui` route and rebuild UI.

## Approach taken vs rejected (preview; full record at item 10)

- **Take:** new app `test`, SQL `COUNT` + `GROUP BY` on existing annotation tables. Contained, matches the brief, cheap to measure.
- **Reject:** counting from exported COCO JSON or from ClickHouse events. Export is not “read from the database”. Events are not the annotation tables.
- **Cost of rejecting export:** we must learn CVAT’s job/segment/task and label FKs instead of parsing a file we already uploaded.

## What “done enough to submit” means

Items 1–4 working on the COCO task, three docs present, incremental commits, recording still to do at the end. Stop rather than ship a broken 8–9.
