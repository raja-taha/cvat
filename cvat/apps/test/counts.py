from collections import defaultdict

from django.db.models import Count

from cvat.apps.engine.models import LabeledImage, LabeledShape, LabeledTrack


def count_annotations_by_class(task_id: int) -> list[dict]:
    """Group annotation rows for a task by label. This is the per-class count.

    Shapes, tags and tracks all subclass Annotation and point at Job + Label.
    Job -> Segment -> Task is how CVAT stores that an annotation belongs to a task.
    Skeleton parts (LabeledShape.parent set) are skipped so a skeleton is one shape.
    """
    totals: dict[int, dict] = {}

    shape_qs = LabeledShape.objects.filter(
        job__segment__task_id=task_id,
        parent__isnull=True,
    )
    tag_qs = LabeledImage.objects.filter(job__segment__task_id=task_id)
    track_qs = LabeledTrack.objects.filter(job__segment__task_id=task_id)

    for queryset in (shape_qs, tag_qs, track_qs):
        rows = queryset.values("label_id", "label__name", "label__color").annotate(
            count=Count("id")
        )
        for row in rows:
            entry = totals.setdefault(
                row["label_id"],
                {
                    "label_id": row["label_id"],
                    "name": row["label__name"],
                    "color": row["label__color"],
                    "count": 0,
                },
            )
            entry["count"] += row["count"]

    return sorted(totals.values(), key=lambda item: (-item["count"], item["name"]))


def count_annotations_by_class_and_source(task_id: int) -> list[dict]:
    """Same counts, split by Annotation.source (file, manual, …)."""
    totals: dict[int, dict] = {}

    shape_qs = LabeledShape.objects.filter(
        job__segment__task_id=task_id,
        parent__isnull=True,
    )
    tag_qs = LabeledImage.objects.filter(job__segment__task_id=task_id)
    track_qs = LabeledTrack.objects.filter(job__segment__task_id=task_id)

    for queryset in (shape_qs, tag_qs, track_qs):
        rows = queryset.values("label_id", "label__name", "label__color", "source").annotate(
            count=Count("id")
        )
        for row in rows:
            entry = totals.setdefault(
                row["label_id"],
                {
                    "label_id": row["label_id"],
                    "name": row["label__name"],
                    "color": row["label__color"],
                    "count": 0,
                    "by_source": defaultdict(int),
                },
            )
            source = row["source"] or "unknown"
            entry["by_source"][source] += row["count"]
            entry["count"] += row["count"]

    result = []
    for item in totals.values():
        result.append(
            {
                "label_id": item["label_id"],
                "name": item["name"],
                "color": item["color"],
                "count": item["count"],
                "by_source": dict(item["by_source"]),
            }
        )
    return sorted(result, key=lambda item: (-item["count"], item["name"]))
