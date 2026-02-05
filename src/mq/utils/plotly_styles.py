"""A set of plotly "aliases" to apply consistent styling."""

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


def style_figure(fig, **kwargs):
    """Apply standard styling. kwargs can override layout or axes."""

    def merge_and_filter(defaults, overrides):
        """Merge dicts and remove None values."""
        result = {**defaults, **overrides}
        return {k: v for k, v in result.items() if v is not None}

    layout_defaults = dict(
        hovermode="closest",
        margin=dict(t=20, b=40, autoexpand=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(type="date", tickformat="%Y-%m-%d"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_layout(**merge_and_filter(layout_defaults, kwargs.get("layout", {})))
    fig.update_xaxes(**merge_and_filter(AXIS_DEFAULTS, kwargs.get("xaxis", {})))
    fig.update_yaxes(**merge_and_filter(AXIS_DEFAULTS, kwargs.get("yaxis", {})))

    return fig
