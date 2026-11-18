import pytest

from repairrouter.data import generate_requests, load_requests, write_requests


def test_synthetic_requests_are_deterministic():
    assert generate_requests(seed=73) == generate_requests(seed=73)


def test_request_round_trip(tmp_path):
    original = generate_requests(seed=73)
    path = tmp_path / "requests.csv"
    write_requests(original, path)
    assert load_requests(path) == original


def test_loader_rejects_unknown_category(tmp_path):
    path = tmp_path / "requests.csv"
    path.write_text(
        "request_id,text,category,urgency\n"
        "REQ-1,The kitchen faucet is leaking badly,unknown,routine\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unsupported category"):
        load_requests(path)


def test_loader_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "requests.csv"
    path.write_text(
        "request_id,text,category,urgency\n"
        "REQ-1,The kitchen faucet is leaking badly,plumbing,routine\n"
        "REQ-1,A ceiling light is flickering, electrical,routine\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate request_id"):
        load_requests(path)
