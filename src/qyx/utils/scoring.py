"""User state management/persistence."""

import logging
from types import SimpleNamespace as Sns

log = logging.getLogger(__name__)


def score_metric(args: Sns, metric_path: str, value: float) -> Sns:
    """Score a metric value according to configured thresholds.

    Returns:
        Sns with score, grade, and color
    """
    metric_config = args.config.get(metric_path)
    if not metric_config:
        # Fallback to default if not configured
        log.warning(f"Sorry, couldn't find a scoring configuration for {metric_path=}!")
        return Sns(score=value, grade="?", color="#6b7280")

    if "thresholds" not in metric_config:
        log.warning(f"Sorry, couldn't find a 'thresholds' section in {metric_path=}!")
        return Sns(score=value, grade="?", color="#6b7280")

    grade, color = find_grade(value, metric_config["thresholds"])

    if grade == "?":
        log.warning(f"Configuration issue? Unable to map {value=} to a value metric grading bucket: {metric_path=}")

    return Sns(score=value, grade=grade, color=color)


def find_grade(value: float, thresholds: list[dict]) -> tuple[str, str]:
    """Find the appropriate grade and color for a value.

    Value is checked against each threshold range [min, max).
    """
    for threshold in thresholds:
        min_val = threshold.get("min", 0)
        max_val = threshold.get("max", float("inf"))

        # Convert "inf" strings to float
        if min_val == "inf":
            min_val = float("inf")
        if max_val == "inf":
            max_val = float("inf")

        # Check if value falls in this range [min-inclusive, max-below]
        if min_val <= value < max_val:
            return threshold.get("grade"), threshold.get("color")

    # Fallback if no threshold matched
    return "?", "#6b7280"
