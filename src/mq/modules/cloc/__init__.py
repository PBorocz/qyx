"""..."""

MODULE = "cloc"


def get_ingest_command(project_path: str, sub_module: str = None) -> list[str]:
    """Return the command sent to subprocess to directly perform a CLOC operation."""
    return [
        "cloc",
        "--include-lang=Python",
        "--by-file",
        "--json",
        "--exclude-dir=.venv",
        project_path,
    ]


def get_parse_method_name(sub_module: str = None) -> list[str]:
    """Return the name of method to parse this module's JSON output."""
    return "parse_json"


################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  CLOC Runs without data aren't valid and can be cleaned out.
RESULTS_REQUIRED = True
