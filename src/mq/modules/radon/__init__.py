"""..."""

MODULE = "radon"
COLORS = dict(positive="green", negative="red", neutral="white")

################################################################################################@
# Are results "required" for a Run to be valid?
################################################################################################@
# In this case,  Radon Runs without data aren't valid and can be cleaned out.
RESULTS_REQUIRED = True
