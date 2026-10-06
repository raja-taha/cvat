# Objectives

Machine and method filled in as we go. Target chosen before measuring, not after.

## Environment (fill when measuring)

| Field | Value |
| --- | --- |
| OS | Windows 10 (build 26200), Docker Desktop |
| CPU | _to be recorded_ |
| RAM | _to be recorded_ |
| CVAT clone SHA | `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5` |
| Sample | COCO 2017 val, image count _to be recorded_ |

## MO-1 — annotation-count endpoint latency

**What is measured.** Wall time of `GET /api/test/tasks/<id>/annotation-counts` from the host, authenticated, against the local Docker stack, for the COCO sample task.

**How.** `curl.exe -w "%{time_total}\n" -o NUL -s` (or equivalent) after a login cookie/token. Same URL five times in a row. No warmup discarded; all five runs kept.

**Target.** Median of 5 runs at or below **200 ms**.

**Why that number.** The handler is a grouped `COUNT` on annotation rows already in Postgres, not a dataset export. On a local compose stack that should be well under a second. 200 ms is tight enough that an N+1 query or loading every shape into Python would miss it, and loose enough that one Docker network hop is allowed.

**Conditions.** Chrome or curl from the same machine, local `docker compose` stack, sample task only, cache not involved (API has no HTTP cache). Nothing else heavy running, stated at measurement time.

**Not included.** Cold start after `docker compose up`. Video tasks. First request after a server restart. The UI chart render.

**Rules.** Raw output pasted below. Report median and spread (min, max). One number alone is not a measurement.

### Raw output

_Not measured yet._

### Result

_Pending._

## Sample data note

Use as many COCO val2017 images as this machine handles. Record the count here after import, and confirm a job shows labelled boxes before calling MO-1 done.
