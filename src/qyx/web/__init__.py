"""Common web rendering chunks."""

from fasthtml import common as fh

from qyx.tools.base import Project, State


def render_project_selector(request, hx_get: str):
    """Return a form to allow selection over all projects."""
    fh_select = get_project_select(request, hx_get)
    return fh.Form(fh.Fieldset(fh_select))


def get_project_select(request, hx_get: str):
    """Return a select widget with options across all projects, reflecting state.

    We keep this separate as some tools will want to create their own "composite"
    Form Fieldset (e.g. Radon) and this allows them to work while simpler tools
    can use the complete Form above.
    """
    projects = Project.select().order_by(Project.name)
    if not projects:
        return None

    # Convert our project(s) into selector items..
    elif len(projects) > 1:
        last_project = State.lookup("project")
        fh_select_items = [fh.Option("Project...", value="")]
        for project in projects:
            option_kwargs = dict(value=str(project.id))
            if last_project and project.name.lower() == last_project.lower():
                option_kwargs["selected"] = True
            fh_select_items.append(
                fh.Option(project.name, **option_kwargs),
            )

    elif len(projects) == 1:
        project = projects[0]
        fh_select_items = [fh.Option(project.name, value=str(project.id), selected=True)]

    return fh.Select(
        *fh_select_items,
        name="project",
        aria_label="Select your project...",
        hx_get=hx_get,  # HTMX endpoint
        hx_target="#page-body-content",  # Where to update
        hx_swap="innerHTML",  # How to update
        hx_trigger="load, change",  # Trigger on page load *AND* selection change
        hx_include="[name='analysis']",  # Include analysis selector value
    )
