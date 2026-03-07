"""Render the "home"/summary page."""

import logging
from types import SimpleNamespace as Sns

from bottle import request

from qyx.constants import ViewContext as Vc
from qyx.tools.base import Project, Scan, State
from qyx.tools.common import import_method
from qyx.web.page import get_project_selector, render_page, render_template


log = logging.getLogger(__name__)


def dashboard_view(template: str = "base::dashboard_page.html") -> str:
    """Render the home/summary/Dashboard page."""
    project_options, _ = get_project_selector()
    return render_page("QYX Home", template, project_options=project_options)


def dashboard_view_content(template: str = "base::dashboard_body.html") -> str:
    """Supply the body portion of the Dashboard page on a project update."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_template("base::_no_projects_yet.html")

    State.update(args, project=project.name)  # Remember for next instantiation!

    context = Sns(as_of_dates={}, analyses=[])

    for ta_ in args.config.get("renderers.web.dashboard.analysis_order", ()):
        (tool, analysis) = ta_.split(":")
        scan = Scan.get_most_recent(project, tool, analysis)
        if scan:
            # First, lookup the appropriate *VIEW* method to use from the respective tool's web views.
            # --> Relying upon NAMING CONVENTION's here!
            method = import_method(f"qyx.tools.{tool}.web:view_{analysis}_0")
            if not method:
                # If there isn't a view method, lookup the appropriate *QUERY* method to use from the tool's models.
                # --> Relying upon NAMING CONVENTION's here!
                method = import_method(f"qyx.tools.{tool}.models:query_{analysis}_0")
                if not method:
                    log.error(f"Unable to render {ta_} for dashboard")
                    continue

            ##################################
            # Call it to populate our context!
            ##################################
            ctx = method(args=args, scan=scan, context=Vc.DASHBOARD)
            setattr(context, f"{analysis}_0", ctx)

            # Mark which dates we processed each analysis upon..
            context.as_of_dates[analysis] = scan.as_of_display(collapse_today=True)

            # Return which combinations we actually got data for!
            context.analyses.append((tool, analysis))

    return render_template(template, **context.__dict__)
