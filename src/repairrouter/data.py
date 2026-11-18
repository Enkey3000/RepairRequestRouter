"""Synthetic maintenance request generation and tabular I/O."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

CATEGORIES = ("plumbing", "electrical", "hvac", "appliance", "structural", "safety")
URGENCY = ("routine", "priority", "emergency")

CATEGORY_TEAM = {
    "plumbing": "Plumbing",
    "electrical": "Electrical",
    "hvac": "Climate systems",
    "appliance": "Appliance",
    "structural": "Facilities",
    "safety": "Safety response",
}


@dataclass(frozen=True)
class Request:
    request_id: str
    text: str
    category: str
    urgency: str


TEMPLATES = {
    "plumbing": [
        "A faucet is leaking under the kitchen sink.",
        "The bathroom toilet keeps running and will not stop.",
        "Water is dripping from the pipe near the utility closet.",
        "A drain is clogged and water is backing up in the shower.",
    ],
    "electrical": [
        "An outlet in the office is not supplying power.",
        "A ceiling light flickers whenever it is switched on.",
        "The circuit breaker trips repeatedly under normal use.",
        "A wall switch feels warm and has started buzzing.",
    ],
    "hvac": [
        "The heating system is blowing cold air into the classroom.",
        "A room thermostat is not controlling the air temperature.",
        "The ventilation fan makes a loud rattling noise.",
        "The air conditioning unit is leaking and not cooling.",
    ],
    "appliance": [
        "The breakroom refrigerator is not keeping food cold.",
        "The dishwasher does not drain after a wash cycle.",
        "A microwave display turns on but the unit will not heat.",
        "The laundry dryer stops before the clothes are dry.",
    ],
    "structural": [
        "There is a cracked tile in the main hallway.",
        "A door does not close and the frame appears warped.",
        "A ceiling panel has become loose above the desk.",
        "The stair handrail moves when someone holds it.",
    ],
    "safety": [
        "A strong smoke smell is coming from an electrical panel.",
        "Smoke is visible near the storage room and the area should be evacuated.",
        "Water is pooling beneath exposed wiring in the corridor.",
        "A carbon monoxide alarm is sounding in the occupied building.",
    ],
}

EMERGENCY_PHRASES = (
    "Smoke is visible",
    "carbon monoxide",
    "exposed wiring",
    "strong smoke smell",
)


def generate_requests(seed: int = 73, count_per_category: int = 18) -> list[Request]:
    rng = random.Random(seed)
    prefix = ["Please help:", "Maintenance needed:", "Issue report:", "Work order:"]
    requests: list[Request] = []
    for category in CATEGORIES:
        templates = TEMPLATES[category]
        for index in range(count_per_category):
            text = templates[index % len(templates)]
            if index % 3 == 1:
                text = f"{rng.choice(prefix)} {text}"
            if index % 5 == 4:
                text = text + " Please inspect it today."
            urgency = "routine"
            if category == "safety":
                urgency = "emergency"
            elif index % 4 == 3 or index % 7 == 6:
                urgency = "priority"
            requests.append(
                Request(
                    request_id=f"REQ-{len(requests) + 1:04d}",
                    text=text,
                    category=category,
                    urgency=urgency,
                )
            )
    return requests


def write_requests(requests: list[Request], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("request_id", "text", "category", "urgency"),
        )
        writer.writeheader()
        for request in requests:
            writer.writerow(
                {
                    "request_id": request.request_id,
                    "text": request.text,
                    "category": request.category,
                    "urgency": request.urgency,
                }
            )


def load_requests(path: Path) -> list[Request]:
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    requests: list[Request] = []
    ids: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"request_id", "text", "category", "urgency"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            request_id = row["request_id"].strip()
            text = " ".join(row["text"].split())
            category = row["category"].strip().lower()
            urgency = row["urgency"].strip().lower()
            if not request_id or request_id in ids:
                raise ValueError(f"Empty or duplicate request_id: {request_id!r}")
            if len(text) < 10:
                raise ValueError(f"Request text is too short: {request_id}")
            if category not in CATEGORIES:
                raise ValueError(f"Unsupported category: {category}")
            if urgency not in URGENCY:
                raise ValueError(f"Unsupported urgency: {urgency}")
            requests.append(Request(request_id, text, category, urgency))
            ids.add(request_id)
    if not requests:
        raise ValueError("Request CSV contains no rows")
    return requests
