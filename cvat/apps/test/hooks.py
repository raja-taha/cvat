"""Wire live analytics updates into CVAT annotation writes.

Imports normally run in one big atomic transaction on a worker, so the analytics
page only sees counts when the whole job finishes. We:
  1. flush annotations to the DB in small chunks
  2. drop the outer import transaction so each chunk commits
  3. publish Redis events after each commit
  4. report RQ progress so the tasks-page progress bar moves
"""

from __future__ import annotations

from functools import wraps

from cvat.apps.engine.models import Job
from cvat.apps.test.notify import publish_task_changed

# Flush to Postgres often enough that a live chart can grow during import.
STREAM_ANNO_CHUNK = 200


def _task_id_from_job(job_id: int) -> int | None:
    try:
        return Job.objects.select_related("segment").values_list("segment__task_id", flat=True).get(
            pk=job_id
        )
    except Job.DoesNotExist:
        return None


def _after_job(job_id: int) -> None:
    task_id = _task_id_from_job(job_id)
    if task_id is not None:
        publish_task_changed(task_id)


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _update_import_progress(done: int, total: int | None = None) -> None:
    try:
        from rq import get_current_job

        from cvat.apps.engine.rq import ImportRQMeta
    except Exception:
        return

    rq_job = get_current_job()
    if rq_job is None:
        return
    try:
        meta = ImportRQMeta.for_job(rq_job)
        if total and total > 0:
            meta.progress = min(1.0, float(done) / float(total))
            meta.status = f"Importing annotations… {done}/{total}"
        else:
            current = float(meta.progress or 0.0)
            meta.progress = min(0.95, max(current, 0.05) + 0.04)
            meta.status = f"Importing annotations… {done} written"
        meta.save()
    except Exception:
        return


def install_annotation_hooks() -> None:
    from cvat.apps.dataset_manager import bindings
    from cvat.apps.dataset_manager import task as dm_task
    from cvat.apps.engine.plugins import add_plugin

    # Smaller in-memory batches → create_callback runs many times during COCO import.
    orig_common_init = bindings.CommonData.__init__

    def common_init(self, *args, **kwargs):
        orig_common_init(self, *args, **kwargs)
        self._MAX_ANNO_SIZE = STREAM_ANNO_CHUNK

    bindings.CommonData.__init__ = common_init

    orig_handle = dm_task.handle_annotations_change
    written = {"n": 0}

    def handle_annotations_change(instance, annotations, action, **kwargs):
        result = orig_handle(instance, annotations, action, **kwargs)
        task_id = getattr(getattr(instance, "segment", None), "task_id", None)
        if task_id is not None and action in {"create", "update", "delete"}:
            shapes = 0
            if isinstance(annotations, dict):
                shapes = (
                    len(annotations.get("shapes") or [])
                    + len(annotations.get("tags") or [])
                    + len(annotations.get("tracks") or [])
                )
            written["n"] += max(shapes, 1)
            _update_import_progress(written["n"])
            publish_task_changed(task_id)
        return result

    dm_task.handle_annotations_change = handle_annotations_change

    def after_job(*args, **kwargs):
        if args:
            _after_job(args[0])

    def after_task(*args, **kwargs):
        if args:
            publish_task_changed(args[0])

    for name in ("put_job_data", "patch_job_data", "delete_job_data"):
        try:
            add_plugin(name, after_job, "after", exc_ok=True)
        except Exception:
            pass
    for name in ("put_task_data", "patch_task_data", "delete_task_data"):
        try:
            add_plugin(name, after_task, "after", exc_ok=True)
        except Exception:
            pass

    orig_put_job = dm_task.put_job_data
    orig_patch_job = dm_task.patch_job_data
    orig_delete_job = dm_task.delete_job_data
    orig_put_task = dm_task.put_task_data
    orig_patch_task = dm_task.patch_task_data
    orig_delete_task = dm_task.delete_task_data

    def put_job_data(pk, data, *, db_job=None):
        result = orig_put_job(pk, data, db_job=db_job)
        _after_job(pk)
        return result

    def patch_job_data(pk, data, action, *, db_job=None):
        result = orig_patch_job(pk, data, action, db_job=db_job)
        _after_job(pk)
        return result

    def delete_job_data(pk, *, db_job=None):
        task_id = _task_id_from_job(pk)
        orig_delete_job(pk, db_job=db_job)
        if task_id is not None:
            publish_task_changed(task_id)

    def put_task_data(pk, data):
        result = orig_put_task(pk, data)
        publish_task_changed(pk)
        return result

    def patch_task_data(pk, data, action):
        result = orig_patch_task(pk, data, action)
        publish_task_changed(pk)
        return result

    def delete_task_data(pk):
        orig_delete_task(pk)
        publish_task_changed(pk)

    dm_task.put_job_data = put_job_data
    dm_task.patch_job_data = patch_job_data
    dm_task.delete_job_data = delete_job_data
    dm_task.put_task_data = put_task_data
    dm_task.patch_task_data = patch_task_data
    dm_task.delete_task_data = delete_task_data

    # Drop the outer @transaction.atomic so each patch_job_data chunk commits and
    # becomes visible to the analytics page / WebSocket subscribers immediately.
    bare_import_task = _unwrap(dm_task.import_task_annotations)
    bare_import_job = _unwrap(dm_task.import_job_annotations)

    @wraps(bare_import_task)
    def import_task_annotations(*args, **kwargs):
        written["n"] = 0
        _update_import_progress(0)
        result = bare_import_task(*args, **kwargs)
        task_id = args[1] if len(args) > 1 else kwargs.get("task_id")
        if task_id is not None:
            _update_import_progress(written["n"] or 1, written["n"] or 1)
            publish_task_changed(task_id)
        return result

    @wraps(bare_import_job)
    def import_job_annotations(*args, **kwargs):
        written["n"] = 0
        _update_import_progress(0)
        result = bare_import_job(*args, **kwargs)
        job_id = args[1] if len(args) > 1 else kwargs.get("job_id")
        if job_id is not None:
            _after_job(job_id)
        return result

    dm_task.import_task_annotations = import_task_annotations
    dm_task.import_job_annotations = import_job_annotations
