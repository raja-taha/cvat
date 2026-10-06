# Objectives

Target chosen before measuring (200 ms). Numbers below are from this machine.

## Environment

| Field | Value |
| --- | --- |
| OS | Windows 10 (build 26200), Docker Desktop |
| CPU | Intel Core i7-7820HQ @ 2.90 GHz |
| RAM | 16 GB (17054511104 bytes reported) |
| CVAT clone SHA | `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5` |
| Sample | COCO 2017 val, **200 images** per task (subset the machine handled). Task 1 used for MO-1. |

## MO-1 — annotation-count endpoint latency

**What is measured.** Wall time of `GET /api/test/tasks/1/annotation-counts` from the host, authenticated, against the local Docker stack, for the 200-image COCO task.

**How.** `curl.exe -s -o NUL -w "%{time_total}\n"` with `Authorization: Token …` and `Accept: application/vnd.cvat+json; version=2.0`. Same URL five times in a row. No run discarded.

**Target.** Median of 5 runs at or below **200 ms**.

**Why that number.** The handler is grouped `COUNT`s on annotation rows in Postgres, not a dataset export. 200 ms is tight enough that an N+1 query or loading every shape into Python would miss it, and loose enough that one Docker network hop is allowed.

**Conditions.** curl from this Windows host, local `docker compose` stack, task 1 (1,468 annotations, 77 classes). Measured 6 Oct 2026 after the server had been up (not a cold start).

**Not included.** Cold start after `docker compose up`. Video tasks. First request after a server restart. The HTML chart render.

### Raw output

`curl.exe` `%{time_total}` (seconds), five consecutive runs:

```
0.068034
0.062747
0.062742
0.070785
0.069209
```

### Result

| | |
| --- | --- |
| Converted to ms | 68.034, 62.747, 62.742, 70.785, 69.209 |
| Median | **68.0 ms** |
| Spread | min **62.7 ms**, max **70.8 ms** |
| Target | ≤ 200 ms median |
| Outcome | **Met** (median 68.0 ms) |

## Sample data note

200 COCO val2017 images. Jobs show labelled boxes after importing `coco/annotations/instances_val2017_subset.json` (the full val JSON does not match a 200-frame task). Task 1 SQL check: `engine_labeledshape` count for label `person`, `parent_id IS NULL`, task 1 = **434**, matching the API (`person`, 434, `by_source.file`).
