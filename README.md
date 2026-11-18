# RepairRequestRouter

**Turn unstructured maintenance requests into reviewable service routes.**

RepairRequestRouter is a local natural-language portfolio prototype for classifying
synthetic maintenance requests into plumbing, electrical, HVAC, appliance,
structural, or safety queues. It combines TF-IDF text features, logistic regression,
confidence-based human review, and conservative safety-keyword escalation.

> **Scope:** All requests and routing outcomes are synthetic. The project does not
> detect real emergencies, issue service guarantees, or replace an authorized
> maintenance dispatcher.

## Executive summary and case study

A fictional property team receives short, inconsistent work-order descriptions.
Messages currently require staff to read and route every request manually. The
prototype demonstrates a low-cost text triage pipeline that predicts a service team,
withholds low-confidence cases for review, and escalates clear safety language.
It is a software proof, not a validated operational dispatch system.

## Quick start (PowerShell)

Requires Python 3.10 or later.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
repairrouter generate --output data/sample/requests.csv --seed 73
repairrouter evaluate --input data/sample/requests.csv --output-dir build/reports
python -m pytest
ruff check .
```

Run one request without relying on the installed script:

```powershell
$env:PYTHONPATH = "src"
python -m repairrouter.cli classify "Smoke is visible near an electrical panel."
```

The evaluation writes `build/reports/evaluation.json` and
`build/reports/review_queue.csv`.

## Data contract

`requests.csv` contains:

- `request_id`: unique synthetic identifier
- `text`: short free-text maintenance description
- `category`: plumbing, electrical, hvac, appliance, structural, or safety
- `urgency`: routine, priority, or emergency

The loader rejects duplicate IDs, short text, unsupported categories, and unsupported
urgency values.

## Five assumptions and solutions

1. **Short descriptions contain enough category signals.** Use TF-IDF word and
   character n-grams.
2. **Predictions may be wrong.** Route low-confidence cases to a human queue.
3. **Safety language requires extra care.** Apply conservative safety escalation rules.
4. **Text drift will occur.** Use a versioned model, temporal evaluation, and audit
   queue.
5. **Routing is not final dispatch.** Report a team and review status; authorized staff
   retain the decision.

## Foreseeable questions

**Does the model understand emergency situations?** It uses synthetic category
learning plus explicit safety phrases. It is not an emergency detection system.

**What happens if confidence is low?** The request is sent to `human_review`.

**Why TF-IDF instead of a large language model?** It is transparent, inexpensive,
fully local, and suitable for a compact demonstration.

**Can this access live building systems?** No. The starter is offline and CSV-based.

**Are synthetic metrics proof of real accuracy?** No. Real performance is unknown and
must be established with authorized, temporally valid, reviewed data.

## Automation, optimization, and potential cost savings

- **Automation:** Batch route approved work-order text and generate a human-review queue.
- **Optimization:** Add active-learning labels only for reviewed, de-identified examples.
- **Potential savings:** Faster initial routing could reduce staff sorting time and
  repeated handoffs. This project claims no measured savings or response-time impact.

## Project layout

```text
RepairRequestRouter/
├── .github/workflows/ci.yml
├── data/sample/requests.csv
├── docs/methodology.md
├── reports/
├── src/repairrouter/
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT. See [LICENSE](LICENSE).
