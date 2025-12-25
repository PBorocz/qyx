"""..."""

MODULE: str = "ruff"
COLORS = dict(positive="red", negative="green", neutral="white")

# Command sent to subprocess to directly perform a CLOC operation.
# (will be post-pended with the respective runtime directory)
INGEST_ARGS = [
    "ruff",
    "check",
    "--exit-zero",
    "--output-format=json",
]

################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  Ruff Runs without data aren perfectly valid! (rare but certainly valid)
RESULTS_REQUIRED = False
