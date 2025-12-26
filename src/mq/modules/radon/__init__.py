"""..."""

MODULE = "radon"
COLORS = dict(positive="green", negative="red", neutral="white")

RADON_SUB_MODULE_PARSE_METHODS = dict(
    cc="parse_json_cc",
    hal="parse_json_hal",
    mi="parse_json_mi",
    raw="parse_json_raw",
)


def get_ingest_command(project_path: str, sub_module: str = None) -> list[str]:
    """Return the command sent to subprocess to directly perform an ingest operation."""
    return [
        "uvx",
        "radon",
        sub_module,
        "--json",
        project_path,
    ]


def get_parse_method_name(sub_module: str) -> list[str]:
    """Return the name of method to parse this module's JSON output."""
    return f"parse_json_{sub_module.lower()}"


################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  Radon Runs without data aren't valid and can be cleaned out.
RESULTS_REQUIRED = True
