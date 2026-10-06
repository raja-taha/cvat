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

    queries = (
        (
            LabeledShape.objects.filter(job__segment__task_id=task_id, parent__isnull=True),
            "shape",
        ),
        (LabeledImage.objects.filter(job__segment__task_id=task_id), "tag"),
        (LabeledTrack.objects.filter(job__segment__task_id=task_id), "track"),
    )

    for queryset, kind in queries:
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
                    "by_kind": defaultdict(int),
                },
            )
            source = row["source"] or "unknown"
            entry["by_source"][source] += row["count"]
            entry["by_kind"][kind] += row["count"]
            entry["count"] += row["count"]

    result = []
    for item in totals.values():
        result.append(
            {
                "label_id": item["label_id"],
                "name": item["name"],
                "color": item["color"] or "#1890ff",
                "count": item["count"],
                "by_source": dict(item["by_source"]),
                "by_kind": dict(item["by_kind"]),
            }
        )
    return sorted(result, key=lambda item: (-item["count"], item["name"]))


def count_annotations_by_class_and_source(task_id: int) -> list[dict]:
    """Same payload as count_annotations_by_class; source split is always included."""
    return count_annotations_by_class(task_id)
