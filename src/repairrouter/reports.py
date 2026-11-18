"""Write machine-readable and review-friendly routing reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_reports(
    metrics: dict[str, Any],
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "evaluation.json"
    routing_path = output_dir / "review_queue.csv"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    fields = (
        "request_id",
        "text",
        "actual_category",
        "predicted_category",
        "actual_urgency",
        "confidence",
        "review_status",
        "review_reason",
    )
    with routing_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return metrics_path, routing_path
