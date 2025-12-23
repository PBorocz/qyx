"""..."""

MODULE: str = "ruff"
COLORS = dict(positive="red", negative="green", neutral="white")

################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  Ruff Runs without data aren perfectly valid! (rare but certainly valid)
RESULTS_REQUIRED = False
