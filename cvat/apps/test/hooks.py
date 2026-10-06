from cvat.apps.engine.models import Job
from cvat.apps.test.notify import publish_task_changed


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


def install_annotation_hooks() -> None:
    from cvat.apps.dataset_manager import task as dm_task

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
