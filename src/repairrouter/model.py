"""Local TF-IDF text routing and confidence-based review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from repairrouter.data import Request


@dataclass(frozen=True)
class Evaluation:
    accuracy: float
    balanced_accuracy: float
    test_requests: int
    review_threshold: float
    review_count: int
    review_rate: float
    per_category: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDecision:
    predicted_category: str
    team: str
    urgency: str
    confidence: float
    review_status: str


class RepairRouter:
    """Fit a local TF-IDF/logistic classifier for maintenance text."""

    def __init__(self, *, seed: int = 41) -> None:
        self.seed = seed
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self.classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=1500,
            random_state=seed,
        )

    def fit(self, requests: Iterable[Request]) -> None:
        items = list(requests)
        if len(items) < 12:
            raise ValueError("At least 12 requests are required")
        matrix = self.vectorizer.fit_transform([item.text for item in items])
        self.classifier.fit(matrix, [item.category for item in items])

    def predict(self, text: str, *, review_threshold: float = 0.50) -> RoutingDecision:
        if not 0 < review_threshold < 1:
            raise ValueError("review_threshold must be between 0 and 1")
        clean = " ".join(text.split())
        if len(clean) < 10:
            raise ValueError("Request text is too short")
        matrix = self.vectorizer.transform([clean])
        probability_row = self.classifier.predict_proba(matrix)[0]
        index = int(probability_row.argmax())
        category = str(self.classifier.classes_[index])
        confidence = float(probability_row[index])
        urgency = "routine"
        lowered = clean.lower()
        emergency_terms = (
            "smoke",
            "carbon monoxide",
            "exposed wiring",
            "sparking",
            "gas leak",
            "electrical fire",
        )
        if category == "safety" or any(term in lowered for term in emergency_terms):
            urgency = "emergency"
            category = "safety"
        elif any(term in lowered for term in ("today", "urgent", "flood", "leak")):
            urgency = "priority"
        from repairrouter.data import CATEGORY_TEAM

        return RoutingDecision(
            predicted_category=category,
            team=CATEGORY_TEAM[category],
            urgency=urgency,
            confidence=round(confidence, 4),
            review_status="human_review" if confidence < review_threshold else "routed",
        )


def route_requests(
    requests: Iterable[Request],
    *,
    review_threshold: float = 0.50,
    seed: int = 41,
) -> tuple[Evaluation, list[dict[str, object]]]:
    if not 0 < review_threshold < 1:
        raise ValueError("review_threshold must be between 0 and 1")
    items = list(requests)
    if len(items) < 20:
        raise ValueError("At least 20 requests are required")
    texts = [item.text for item in items]
    labels = [item.category for item in items]

    train_text, test_text, train_label, test_label, _train_item, test_item = train_test_split(
        texts,
        labels,
        items,
        test_size=0.25,
        random_state=seed,
        stratify=labels,
    )
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )
    train_matrix = vectorizer.fit_transform(train_text)
    test_matrix = vectorizer.transform(test_text)
    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=1500,
        random_state=seed,
    )
    classifier.fit(train_matrix, train_label)
    probabilities = classifier.predict_proba(test_matrix)
    predicted = classifier.predict(test_matrix)

    report = classification_report(
        test_label,
        predicted,
        labels=classifier.classes_.tolist(),
        output_dict=True,
        zero_division=0,
    )
    per_category: dict[str, dict[str, float | int]] = {}
    for category in classifier.classes_.tolist():
        category_report = report[category]
        per_category[category] = {
            "precision": round(float(category_report["precision"]), 4),
            "recall": round(float(category_report["recall"]), 4),
            "f1": round(float(category_report["f1-score"]), 4),
            "support": int(category_report["support"]),
        }

    rows: list[dict[str, object]] = []
    review_count = 0
    for item, actual, prediction, probability_row in zip(
        test_item,
        test_label,
        predicted,
        probabilities,
        strict=True,
    ):
        confidence = float(max(probability_row))
        needs_review = confidence < review_threshold
        if needs_review:
            review_count += 1
        rows.append(
            {
                "request_id": item.request_id,
                "text": item.text,
                "actual_category": actual,
                "predicted_category": prediction,
                "actual_urgency": item.urgency,
                "confidence": round(confidence, 4),
                "review_status": "human_review" if needs_review else "routed",
                "review_reason": "low_confidence" if needs_review else "",
            }
        )

    test_count = len(test_item)
    metrics = Evaluation(
        accuracy=round(float(accuracy_score(test_label, predicted)), 4),
        balanced_accuracy=round(
            float(balanced_accuracy_score(test_label, predicted)),
            4,
        ),
        test_requests=test_count,
        review_threshold=review_threshold,
        review_count=review_count,
        review_rate=round(review_count / test_count, 4),
        per_category=per_category,
    )
    return metrics, rows
