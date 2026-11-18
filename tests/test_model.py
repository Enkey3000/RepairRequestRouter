import csv

import pytest

from repairrouter.data import generate_requests
from repairrouter.model import RepairRouter, route_requests
from repairrouter.reports import write_reports


def test_evaluation_reports_held_out_requests():
    requests = generate_requests(seed=73)
    metrics, rows = route_requests(requests)
    assert metrics.test_requests == 27
    assert len(rows) == metrics.test_requests
    assert set(metrics.per_category) == {
        "plumbing",
        "electrical",
        "hvac",
        "appliance",
        "structural",
        "safety",
    }


def test_review_status_is_conservative():
    requests = generate_requests(seed=73)
    _, rows = route_requests(requests, review_threshold=0.99)
    assert all(row["review_status"] == "human_review" for row in rows)


def test_router_can_classify_and_prioritize_safety():
    requests = generate_requests(seed=73)
    router = RepairRouter(seed=41)
    router.fit(requests)
    decision = router.predict("Smoke is visible near an electrical panel.")
    assert decision.predicted_category == "safety"
    assert decision.team == "Safety response"
    assert decision.urgency == "emergency"


def test_router_rejects_short_input():
    router = RepairRouter()
    router.fit(generate_requests())
    with pytest.raises(ValueError, match="too short"):
        router.predict("broken")


def test_reports_write_metrics_and_queue(tmp_path):
    metrics, rows = route_requests(generate_requests())
    metrics_path, queue_path = write_reports(metrics.to_dict(), rows, tmp_path)
    assert metrics_path.is_file()
    with queue_path.open(newline="", encoding="utf-8") as file:
        assert len(list(csv.DictReader(file))) == len(rows)
