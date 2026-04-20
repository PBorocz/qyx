# Report Module Naming Convention

Files follow the pattern: {metric}_{level}.py

Metrics: cc, hal, mi, raw
Levels: 0, 1, 2, 3, d, h
Example: cc_0.py = Cyclomatic Complexity, Level 0 (Summary)

Each module must export a `report()` function with signature:
   def generate_report(scan: Scan, config: dict) -> str:
	  ...

The CLI dynamically imports based on user's --level argument.

# Steps to Add a New Tool

Here's a good starting order to add a new tool:

## Install Tool

Make your tool is installed and configured to run on it's own from your respective shell prompt (could be installed via `brew`, `uv tool install` or your method of choice).

## Configure tool for registration into QYX

Create the tool registration/configuration `__init__.py` with no reporting, simply allowing for execution and storage of results. This entails analysing the tool's output (preferably JSON) and creating the associated model(s) to store results.

Usually, the easiest way to start this is to copy from an existing tool. For a tool with a single "analysis", copy from ruff or cloc. For a tool with multiple analysis, start from radon.

```bash
cp src/qyx/tools/ruff/__init__.py src/qyx/tools/<newTool>/__init__.py
```

Customise as required. Important consideration to keep in mind: Does a scan of the tool with *no* results received make sense? For example, a scan obo lines of code pretty much required that /some/ data is recieved. Conversely, a `ruff check` scan is perfectly valid to have *no* results! Update results_required in the super.__init__ method appropriately.

Analyses the tools output and create both the underlying storage model and the the associated "parse-store" code to populate. See examples in already supported tools for more information.

Note that *all* tool storage models inherit from `src/qyx/tools/base.py:BaseResultsModel`. This base model provides the following fields, relieving you from having to store them on a tool-specific basis:

- `id`        (AutoField)
- `scan`      (ForeignKeyField(Scan, on_delete="CASCADE"))
- `directory` (CharField)
- `filename`  (CharField)

Files created (all in `tools/<newTool>` directory):
- `__init__.py`
- `models.py`
- `parse.py`

At this point, you should be able to perform a simple capture:

```bash
uv run qyx ingest -n <aProjectName> -a <newTool> -p <aCodeDirectory>
uv run qyx status -n <aProjectName>
```
and see the resulting Request and Scan's stored.

## Add Initial CLI Reporting

Add initial command-line reporting (__init__.py:cli dictionary). I suggest starting with the simplest "summary" report. This entails creating the appropriate query and associated rich terminal display.

Files affected:
- `models.py` -> Add query methods.

Files created:
- `cli.py` -> Add render method for initial summary report.

## Add Web-based Reporting (if desired)

Files created:
- `web.py`
- `templates/*`
