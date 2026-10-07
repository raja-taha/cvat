# Objectives

Target chosen before measuring (200 ms). Numbers below are from this machine.

## Environment

| Field | Value |
| --- | --- |
| OS | Windows 10 (build 26200), Docker Desktop |
| CPU | Intel Core i7-7820HQ @ 2.90 GHz |
| RAM | 16 GB (17054511104 bytes reported) |
| CVAT clone SHA | `d8193c584be9ce6cf9882dad06c0dd920cc0b9c5` |
| Sample | COCO 2017 val, **2000 images** (task 8, `COCO val2017 2000`). Earlier tasks used 200. |

## MO-1 — annotation-count endpoint latency

**What is measured.** Wall time of `GET /api/test/tasks/8/annotation-counts` from the host, authenticated, against the local Docker stack, for the 2000-image COCO task.

**How.** `curl.exe -s -o NUL -w "%{time_total}\n"` with `Authorization: Token …` and `Accept: application/vnd.cvat+json; version=2.0`. Same URL five times in a row. No run discarded.

**Target.** Median of 5 runs at or below **200 ms**.

**Why that number.** The handler is grouped `COUNT`s on annotation rows in Postgres, not a dataset export. 200 ms is tight enough that an N+1 query or loading every shape into Python would miss it, and loose enough that one Docker network hop is allowed.

**Conditions.** curl from this Windows host, local `docker compose` stack, task 8 (16,524 annotations, 80 classes). Measured 6 Oct 2026 after the server had been up (not a cold start). First MO-1 pass was on the 200-image task 1 (median 68.0 ms).

**Not included.** Cold start after `docker compose up`. Video tasks. First request after a server restart. The HTML chart render.

### Raw output

`curl.exe` `%{time_total}` (seconds), five consecutive runs:

```
0.096732
0.081332
0.083745
0.076277
0.091063
```

### Result

| | |
| --- | --- |
| Converted to ms | 96.732, 81.332, 83.745, 76.277, 91.063 |
| Median | **83.7 ms** |
| Spread | min **76.3 ms**, max **96.7 ms** |
| Target | ≤ 200 ms median |
| Outcome | **Met** (median 83.7 ms) |

## Sample data note

**2000** COCO val2017 images on task 8 (`http://localhost:8080/api/test/tasks/8/analytics`). Import used `coco/annotations/instances_val2017_subset.json` filtered to those frames (the full val JSON does not match a subset task). API: `total` **16524**, 80 classes, top `person` **5017** (`by_source.file`). Earlier 200-image tasks (1–4) remain in the stack.
