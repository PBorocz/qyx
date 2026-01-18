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

    grade, color = _find_grade(
        value,
        metric_config["thresholds"],
        metric_config.get("reverse", False),
    )

    return Namespace(score=value, grade=grade, color=color)


def _find_grade(value: float, thresholds: list[dict], reverse: bool = False) -> tuple[str, str]:
    """Find the appropriate grade and color for a value."""
    # log.debug(f"{value=} {reverse=} {thresholds=}")

    def __get_numeric_value(threshold: dict, key: str, default: float = 0) -> float:
        """Convert threshold value to float, handling 'inf' string."""
        val = threshold.get(key, default)
        if val == "inf":
            return float("inf")
        return float(val)

    if reverse:
        # Higher is better (e.g., test coverage)
        for threshold in sorted(
            thresholds,
            key=lambda x: __get_numeric_value(x, "min", 0),
            reverse=True,
        ):
            min_val = threshold.get("min", 0)
            if min_val == "inf":
                min_val = float("inf")
            if value >= float(min_val):
                return threshold["grade"], threshold["color"]

    else:
        # Lower is better (e.g., violations)
        for threshold in sorted(
            thresholds,
            key=lambda x: __get_numeric_value(x, "max", 0),
        ):
            max_val = threshold.get("max", 0)
            if max_val == "inf":
                max_val = float("inf")
            if value < float(max_val):
                return threshold["grade"], threshold["color"]

    # Fallback
    return "?", "#6b7280"
