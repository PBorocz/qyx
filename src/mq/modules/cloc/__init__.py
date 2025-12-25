"""..."""

MODULE = "cloc"

# Command sent to subprocess to directly perform a CLOC operation.
# (will be post-pended with the respective runtime directory)
INGEST_ARGS = [
    "cloc",
    "--include-lang=Python",
    "--by-file",
    "--json",
    "--exclude-dir=.venv",
]


################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  CLOC Runs without data aren't valid and can be cleaned out.
RESULTS_REQUIRED = True
