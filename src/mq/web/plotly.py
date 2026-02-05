"""A set of plotly "aliases" to apply consistent styling."""

################################################################################################
# Default colors (based on Plotly "BOLD")
################################################################################################
SERIES_COLORS = [
    "#7F3C8D",
    "#11A579",
    "#3969AC",
    "#F2B701",
    "#E73F74",
    "#80BA5A",
    "#E68310",
    "#008695",
    "#CF1C90",
    "#f97b72",
    "#4b4b8f",
    "#A5AA99",
]

################################################################################################
# Layout default attributes
################################################################################################
LAYOUT_DEFAULTS = dict(
    hovermode="closest",
    margin=dict(t=20, b=40, autoexpand=True),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(type="date", tickformat="%Y-%m-%d"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

################################################################################################
# Axis default attributes common to both X & Y axes:
################################################################################################
AXIS_DEFAULTS = dict(
    gridcolor="lightgrey",
    griddash="dot",
    gridwidth=1,
    linecolor="lightgrey",
    linewidth=1,
    mirror=True,
    showgrid=True,
    showline=True,
)

# Specific defaults for each one (if any)
X_AXIS_DEFAULTS = AXIS_DEFAULTS.copy()
X_AXIS_DEFAULTS["title"] = "Commit Date"

Y_AXIS_DEFAULTS = AXIS_DEFAULTS.copy()
Y_AXIS_DEFAULTS["rangemode"] = "tozero"


def style_figure(fig, **kwargs):
    """Apply standard styling. kwargs can override layout or either axis."""

    def merge_and_filter(defaults, overrides):
        """Merge dicts and return non-None properties."""
        result = {**defaults, **overrides}
        return {attr: value for attr, value in result.items() if value is not None}

    fig.update_layout(**merge_and_filter(LAYOUT_DEFAULTS, kwargs.get("layout", {})))

    fig.update_xaxes(**merge_and_filter(X_AXIS_DEFAULTS, kwargs.get("xaxis", {})))

    fig.update_yaxes(**merge_and_filter(Y_AXIS_DEFAULTS, kwargs.get("yaxis", {})))

    return fig
