"""Common web rendering chunks."""

from dataclasses import dataclass

from qyx.tools.base import Project, Request, Scan, State


@dataclass(frozen=True)
class Option:
    """Represents an option to be rendered into a select widget."""

    value: str
    display: str
    selected: bool = False


def get_project_selector(analysis: str | list[str] = None) -> tuple[list[Option], Project | None]:
    """Return a form to allow selection over all projects that have every had a scan for the specified analysis."""
    projects = Project.select().join(Request).join(Scan).distinct().order_by(Project.name)
    if analysis:
        if isinstance(analysis, str):
            projects = projects.where(Scan.analysis == analysis)
        else:
            projects = projects.where(Scan.analysis.in_(analysis))

    ################################################################################
    # Case 1: No projects found! (very unusual case)
    ################################################################################
    if len(projects) == 0:
        return ([], None)

    ################################################################################
    # Case 2: Just a single project available.
    ################################################################################
    if len(projects) == 1:
        project = projects[0]
        options = [Option(value=str(project.id), display=project.name, selected=True)]
        return options, project

    ################################################################################
    # Case 3: Multiple projects case...
    ################################################################################
    options = [Option(display="Project...", value="")]
    last_project = State.lookup("project")

    # First pass: lookup the last_project (also to handle the case if it's disappeared!)
    selected_project = None
    if last_project:
        for project in projects:
            if last_project.lower() == project.name.lower():
                selected_project = project
                break

    # If no match found (or no last_project), default to first
    if selected_project is None:
        selected_project = projects[0]

    # Build options with correct selection
    for project in projects:
        selected = project == selected_project
        options.append(Option(value=str(project.id), display=project.name, selected=selected))

    return options, selected_project


def get_scan_selector(project: Project, analysis: str | list[str] = None) -> tuple[list[Option], Scan | None]:
    """Return a form to allow selection over all scans available for the specified analysis."""
    l_analyses = [analysis] if isinstance(analysis, str) else analysis
    scans = (
        Scan.select()
        .join(Request)
        .join(Project)
        .where(
            Request.project == project,
            Scan.analysis.in_(l_analyses),
        )
        .distinct()
        .order_by(
            Scan.as_of.desc(),
        )
    )

    ################################################################################
    # Case 1: No scans found for the project!
    ################################################################################
    if len(scans) == 0:
        return ([], None)

    ################################################################################
    # Case 2: Only a single scan found for the project
    ################################################################################
    if len(scans) == 1:
        scan = scans[0]
        if scan.git_commit_message:
            display = f"{scan.as_of_display()} - {scan.git_commit_message}"
        else:
            display = f"{scan.as_of_display()}"
        option = Option(value=str(scan.id), display=display, selected=True)
        return ([option], scan)

    ################################################################################
    # Case 3: *Multiple* scans found for the project (normal case)
    ################################################################################
    options = [Option(display="Scan...", value="")]
    last_scan = State.lookup("scan")
    selected_scan = None

    # First pass: lookup the last_scan (also to handle the case if it's disappeared!)
    selected_scan = None
    if last_scan:
        for scan in scans:
            if int(last_scan) == scan.id:
                selected_scan = scan
                break

    # If no match found (or no last_scan), default to first
    if selected_scan is None:
        selected_scan = scans[0]

    # Build options with correct selection
    for scan in scans:
        selected = scan == selected_scan
        if scan.git_commit_message:
            display = f"{scan.as_of_display()} - {scan.git_commit_message}"
        else:
            display = f"{scan.as_of_display()}"
        options.append(Option(value=str(scan.id), display=display, selected=selected))

    return options, selected_scan


def get_analysis_selector() -> list[Option]:
    """Return a form to allow selection over all analyses for the specified tool."""
    # FIXME: Make this dynamic and thus tool specific (right now, specific to Radon only!!)
    analyses = (
        ("raw", "Raw Metrics"),
        ("mi", "Maintainability Index"),
        ("hal", "Halstead Complexity Measures"),
        ("cc", "Cyclomatic Complexity"),
    )
    last_analysis = State.lookup("analysis")
    options = []
    for value, display in analyses:
        selected = True if last_analysis and value.lower == last_analysis.lower() else False
        options.append(Option(value=str(value), display=display, selected=selected))

    return options
