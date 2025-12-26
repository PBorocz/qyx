"""..."""

MODULE: str = "ruff"
COLORS = dict(positive="red", negative="green", neutral="white")


def get_ingest_command(project_path: str, sub_module: str = None) -> list[str]:
    """Return the command sent to subprocess to directly perform an ingest operation."""
    return [
        "ruff",
        "check",
        "--exit-zero",
        "--output-format=json",
        project_path,
    ]


def get_parse_method_name(sub_module: str = None) -> list[str]:
    """Return the name of method to parse this module's JSON output."""
    return "parse_json"


################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  Ruff Runs without data aren perfectly valid! (rare but certainly valid)
RESULTS_REQUIRED = False
