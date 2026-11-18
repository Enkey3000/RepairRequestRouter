"""Command-line entry points for generating and evaluating repair requests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repairrouter.data import generate_requests, load_requests, write_requests
from repairrouter.model import RepairRouter, route_requests
from repairrouter.reports import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repairrouter",
        description="Route synthetic maintenance requests locally with TF-IDF and logistic regression.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="generate a synthetic request CSV")
    generate.add_argument("--output", type=Path, default=Path("data/sample/requests.csv"))
    generate.add_argument("--seed", type=int, default=73)

    evaluation = commands.add_parser("evaluate", help="evaluate held-out synthetic requests")
    evaluation.add_argument("--input", type=Path, default=Path("data/sample/requests.csv"))
    evaluation.add_argument("--output-dir", type=Path, default=Path("build/reports"))
    evaluation.add_argument("--threshold", type=float, default=0.50)

    classify = commands.add_parser("classify", help="classify one request")
    classify.add_argument("text")
    classify.add_argument("--input", type=Path, default=Path("data/sample/requests.csv"))
    classify.add_argument("--threshold", type=float, default=0.50)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            requests = generate_requests(seed=args.seed)
            write_requests(requests, args.output)
            print(f"Wrote {len(requests)} synthetic requests to {args.output}")
            print("These fictional records are for software demonstration, not live maintenance.")
            return 0

        requests = load_requests(args.input)
        if args.command == "evaluate":
            metrics, rows = route_requests(requests, review_threshold=args.threshold)
            metrics_path, routing_path = write_reports(metrics.to_dict(), rows, args.output_dir)
            print(json.dumps(metrics.to_dict(), indent=2))
            print(f"Metrics: {metrics_path}")
            print(f"Human review queue: {routing_path}")
        else:
            router = RepairRouter()
            router.fit(requests)
            decision = router.predict(args.text, review_threshold=args.threshold)
            print(json.dumps(decision.__dict__, indent=2))
        print(
            "Interpretation: routes and urgency rules are synthetic screening aids. "
            "A human or authorized operations system must make the service decision."
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"repairrouter: error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
