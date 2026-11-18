# Repair routing methodology

## Synthetic case study

RepairRequestRouter treats a maintenance request as short natural-language text and
predicts one of six service categories: plumbing, electrical, HVAC, appliance,
structural, or safety. It is trained on deliberately simple synthetic phrases with
small paraphrase and prefix variations.

## Model

The text baseline uses word and character n-grams from a TF-IDF vectorizer followed
by multinomial logistic regression. Category confidence comes from the classifier
probability. Requests below a configurable confidence threshold enter a human-review
queue instead of receiving an automatic route.

A separate keyword and category safety rule maps smoke, gas, exposed wiring,
sparking, carbon monoxide, and confirmed safety events to Safety response with
emergency urgency. This rule is a conservative fail-safe in the demonstration, not
proof of real emergency detection.

## Evaluation

The primary evaluation uses a reproducible stratified 75/25 split. It reports overall
accuracy, balanced accuracy, per-category precision/recall/F1, and the share routed
to human review. Random- or platform-held-out text is not a real-world service-level
estimate.

## Limitations

- All records are synthetic and repetitive; accuracy may overstate performance on
  real work-order descriptions.
- A 75/25 split does not test time drift, tenant jargon, incomplete notes, duplicate
  reports, attachments, addresses, or multilingual requests.
- Logistic outputs are confidence estimates, not calibrated probabilities.
- Urgency keywords do not replace authorized emergency procedures or live dispatch.
- No employee, resident, or property text is included.

## Responsible deployment

Before production use, obtain approved maintenance records; remove direct identifiers;
perform temporal and building-held-out tests; calibrate confidence; red-team ambiguous
and adversarial wording; and separately validate safety escalation against incident
rates. Keep a human dispatcher responsible for final routing and require explicit
policy for escalation, accessibility, and emergency calls.
