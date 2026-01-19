"""User state management/persistence."""

import logging
from argparse import Namespace

log = logging.getLogger(__name__)


def score_metric(metric_name: str, value: float, configuration: dict) -> Namespace:
    """Score a metric value according to configured thresholds.

    Args:
        metric_name: Name of metric in config (e.g., 'weighted_violations_per_kloc')
        value: The calculated metric value
        configuration: Configuration entry for this metric's scoring (ie. reverse and thresholds)

    Returns:
        Namespace with score, grade, and color
    """
    metric_config = configuration.get(metric_name)
    if not metric_config:
        # Fallback to default if not configured
        log.warning(f"Sorry, couldn't find a scoring configuration for {metric_name=}!")
        return Namespace(score=value, grade="?", color="#6b7280")

    grade, color = find_grade(value, metric_config["thresholds"])

    if grade == "?":
        log.warning(f"Configuration issue? Unable to map {value=} to a value metric grading bucket: {metric_name=}")

    return Namespace(score=value, grade=grade, color=color)


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
