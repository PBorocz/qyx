"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from abc import ABC
from argparse import Namespace
from importlib import import_module
from types import ModuleType
from typing import Callable, TypeAlias

from .base import BaseModel
from qyx.constants import ReportLevel


log = logging.getLogger(__name__)


################################################################################################
# "Tool" data models
################################################################################################
class ToolDimension:
    """Define a "dimension" of a tool, usually for reporting (Cloc, Scc) or also used to *run* the tool (radon)."""

    def __init__(
        self,
        name: str,
        description: str,
        models: tuple[BaseModel],
        cli_option: str = "default",
    ) -> None:
        self.name = name
        self.description = description
        self.cli_option = cli_option
        self.models = models


class AbstractToolConfiguration(ABC):
    """Defines all the semantics of a code quality tool (aka module) supported by this package."""

    def __init__(
        self,
        name: str,
        description: str,
        dimensions: list[ToolDimension],
        ingest_by_dimension: bool = False,
        ingest_latest_only: bool = False,
        **kwargs,
    ) -> "AbstractToolConfiguration":
        """..."""
        # Short name of the tool, e.g. "ruff", "cloc"
        # separating out the module from the name, we can have a tool
        # called "foo" in a directory called "bar")
        self.name: str = name

        # Description, e.g. "Count lines of code", "Type checker", etc.
        self.description: str = description

        # Name of python module directory implementing the tool, e.g. "ruff" obo ../src/qyx/tools/ruff
        self.module: str  # Populated after instantiation

        # Dimensions supported by the tool
        self.dimensions: list[ToolDimension] = dimensions

        # Are dimensions used during ingest? ie. do we ingest separately for each dimension?
        self.ingest_by_dimension: bool = ingest_by_dimension

        # Do we ingest only the *last*/most-recent git commit available?
        self.ingest_latest_only: bool = ingest_latest_only

        # Save any other non-required values sent in...
        for attr, value in kwargs.items():
            setattr(self, attr, value)

        # Setup some methods that help use the tool later on.
        # (we do this up front to help validate tool configuration)
        self.render_cli_module, self.render_cli_method = self._get_render_method("cli")
        self.render_web_module, self.render_web_method = self._get_render_method("web")

        # Setup the report levels available for the tool based on files/methods available.
        self.report_levels = self._get_report_levels()

    def import_component(self, component: str) -> ModuleType:
        """Dynamically import a component from this module."""
        return import_module(f"qyx.tools.{self.module}.{component}")

    def _get_report_levels(self) -> list[str]:
        """Determine what report levels are available for the tool (across all dimensions)."""
        # Note, this doesn't imply that each dimension has a particular report level available!
        report_levels = set()
        for report_level in ReportLevel:
            if report_level == ReportLevel.ALL:
                continue

            try:
                models_module = self.import_component("models")
            except ModuleNotFoundError:
                log.warning("No 'models' module available yet for tool='{self.name}'.")
                continue

            ################################################################################
            # Look first for simple query method by report level (covers most cases)
            ################################################################################
            try:
                query_method_name = f"query_{self.name}_{report_level.value}"
                getattr(models_module, query_method_name)
                # log.debug(f"Found by name: {report_level.value=} -> {query_method_name=}")
                report_levels.add(report_level)
                continue
            except AttributeError:
                ...

            ################################################################################
            # Look by dimension for tools with dimension-based querying
            ################################################################################
            for o_dimension in self.dimensions:
                try:
                    query_method_name = f"query_{o_dimension.name}_{report_level.value}"
                    getattr(models_module, query_method_name)
                    # log.debug(f"Found by dimension: {report_level.value=} -> {query_method_name=}")
                    report_levels.add(report_level)
                    break
                except AttributeError:
                    # Not reporting, we EXPECT many of these to popup!
                    continue

        return list(report_levels)

    def get_ingest_command(
        self,
        args: Namespace,
        relative="",
        absolute="",
        dimension: ToolDimension = None,
    ) -> list[str]:
        """Return the command sent to subprocess to directly perform a "tool" ingest operation."""
        cmd_template = args.config.get(f"tools.{self.name}.command")
        if not cmd_template:
            log.critical(f"Unable to find 'tools.{self.name}.command'")
            return None
        args = dict(relative=relative, absolute=absolute, dimension="")
        if dimension:
            args["dimension"] = dimension.name
        return [part.format(**args) for part in cmd_template]

    def get_parse_save_method(self, *args, **kwargs) -> Callable:
        """Return the method to parse & save this tool's output (usually JSON)."""
        # NOTE:
        # - This implementation is for "single"-dimension tools (ruff, cloc etc.).
        # - For multi ingest-dimension tools (like radon), this method is *OVERRIDDEN* in their respective __init__.py.
        py_parse: ModuleType = self.import_component("parse")
        return getattr(py_parse, "parse_save")

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

    def find_dimension(self, arg_dimension: str) -> ToolDimension | None:
        for o_dimension in self.dimensions:
            if o_dimension.name.lower() == arg_dimension.lower():
                return o_dimension
        return None

    def get_models(self) -> list[BaseModel]:
        """Return a unique list of all storage models used by the tool."""
        model_classes = set()  # May be duplicates for report only dimension tools! (eg. scc)
        for o_dim in self.dimensions:
            for model_class in o_dim.models:
                model_classes.add(model_class)
        return list(model_classes)


ToolType: TypeAlias = AbstractToolConfiguration


class Tools(dict):
    """The collection of all tools is essentially a dict with a few convenience methods."""

    def display_names(self) -> str:
        """Return a nice comma-delimited list of tool names available."""
        return ", ".join(self.names())

    def names(self) -> list[str]:
        """Return the list of tool names, sorted alphabetically."""
        return sorted(self.keys())

    def tools(self) -> list[ToolType]:
        """Return all the tools, sorted alphabetically by tool name."""
        return [self[tool] for tool in self.names()]

    def dimensions(self) -> list[str]:
        """Return all the dimensions available across all tools defined.."""
        dimensions = list()
        for o_tool in self.tools():
            dimensions.extend(o_tool.dimensions)
        return dimensions

    def tools_dimensions(self) -> list[tuple[ToolType, str]]:
        """Return all list of tool & dimension pairs."""
        return_ = list()
        for o_tool in self.tools():
            for dimension in o_tool.dimensions:
                return_.append((o_tool, dimension))
        return return_
