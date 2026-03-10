"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from abc import ABC
from argparse import Namespace
from importlib import import_module
from types import ModuleType
from typing import Callable, Iterator, TypeAlias

from .base import BaseModel
from qyx.constants import ReportLevel as Rl


log = logging.getLogger(__name__)


################################################################################################
# "Tool" data models
################################################################################################
class AbstractToolConfiguration(ABC):
    """Defines all the semantics of a code quality tool (aka module) supported by this package."""

    def __init__(
        self,
        module: str,
        name: str,
        analyses: dict[str, str],
        models: dict[str, BaseModel],
        reports: dict,
        **kwargs,
    ) -> "AbstractToolConfiguration":
        """..."""
        # Name of python module directory implementing the tool, e.g. "ruff" obo ../src/qyx/tools/ruff
        self.module: str = module

        # Short name of the tool, e.g. e.g. "ruff", "cloc", etc. (by
        # separating out the module from the name, we can have a tool
        # called "foo" in a directory called "foobar")
        self.name: str = name

        # Analyses supported by the tool, short value (eg. "mi") -> long description (eg. "Maintainability Index")
        self.analyses: dict[str, str] = analyses

        # Peewee storage model(s) used by analysis (usually a single
        # one per analysis but could be multiple, see RadonHal for example)
        self.models: dict[str, list[BaseModel]] = models

        # Reports available by interface and report-level
        self.reports: dict = reports

        # Are results "required" for a Scan to be valid? (usually yes)
        self.results_required = True

        # Save any other non-required values sent in...
        for attr, value in kwargs.items():
            setattr(self, attr, value)

        # Setup some methods that help use the tool later on.
        # (we do this up front to help validate tool configuration)
        self.render_cli_module, self.render_cli_method = self._get_render_method("cli")
        self.render_web_module, self.render_web_method = self._get_render_method("web")

    def import_component(self, component: str) -> ModuleType:
        """Dynamically import a component from this module."""
        return import_module(f"qyx.tools.{self.module}.{component}")

    def get_ingest_command(self, args: Namespace, relative=None, absolute=None, analysis=None) -> list[str]:
        """Return the command sent to subprocess to directly perform a "tool" ingest operation."""
        cmd_template = args.config.get(f"tools.{self.name}.run.command")
        return [
            part.format(relative=relative or "", absolute=absolute or "", analysis=analysis or "")
            for part in cmd_template
        ]

    def get_parse_method(self, *args, **kwargs) -> Callable:
        """Return the method to parse & save this tool's output (usually JSON)."""
        # NOTE:
        # - This implementation is for "single"-analysis tools (ruff, cloc etc.).
        # - For multi-analysis tools (like radon), this method is *OVERRIDDEN* in their respective __init__.py.
        py_parse: ModuleType = self.import_component("parse")
        return getattr(py_parse, "parse")

    def _get_render_method(self, interface: str) -> tuple[ModuleType | None, Callable | None]:
        """Return the root render method for this tool and the specified interace, e.g. "web" or "cli"."""
        try:
            render_module: ModuleType = self.import_component(interface)
        except ModuleNotFoundError as exc:
            log.warning(f"Sorry, no '{interface}' capabilities available yet for {self.name} ({str(exc).lower()})")
            return None, None

        if not (render_method := getattr(render_module, "render")):
            log.warning(f"{self.name}: Sorry, no 'render' method found in {self.module}'s {interface}.py file!")
            return None, None

        return render_module, render_method

    def iter_reports(self, interface: str) -> Iterator[str, Rl]:
        """Iterator over analysis available for the specified interface."""
        if interface not in self.reports:
            log.warning(f"Sorry, requesting reports for {interface=} that isn't defined for tool: '{self.name}'!")
        for analysis, report_levels in self.reports.get(interface, ()).items():
            for report_level in report_levels:
                yield analysis, report_level


ToolType: TypeAlias = AbstractToolConfiguration


class Tools(dict):
    """Tools are essentially a dict with some convenience methods."""

    def display_names(self) -> str:
        """Return a nice comma-delimited list of tool names available."""
        return ", ".join(self.names())

    def names(self) -> list[str]:
        """Return the list of tool names, sorted alphabetically."""
        return sorted(self.keys())

    def tools(self) -> list[ToolType]:
        """Return all the tools, sorted alphabetically by tool name."""
        return [self[tool] for tool in self.names()]

    def analyses(self) -> list[str]:
        """Return all the analyses available across all tools defined.."""
        analyses = list()
        for o_tool in self.tools():
            analyses.extend(o_tool.analyses.keys())
        return analyses

    def tools_analyses(self) -> list[tuple[ToolType, str]]:
        """Return all list of tool & analysis pairs."""
        return_ = list()
        for o_tool in self.tools():
            for analysis in o_tool.analyses:
                return_.append((o_tool, analysis))
        return return_
