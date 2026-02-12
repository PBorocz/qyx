# QYX - Python Code Quality Data Warehouse

> A comprehensive code quality analysis and visualization platform for Python projects

**QYX** (pronounced "kix" [like the cereal!]) is a proof-of-concept data warehouse that aggregates, analyzes, and reports on multiple code quality metrics for Python projects. It provides both CLI and web interfaces to track code quality over time, including historical git analysis.

## Features

- **Multi-Tool Integration**: Aggregate metrics from tools like CLOC, Ruff, Radon, and custom analyzers.
- **Persistent Storage**: SQLite database for historical tracking and trend analysis.
- **CLI Interface**: Terminal output with detailed reports at multiple levels (Rich)
- **Web Dashboard**: Interactive dashboard (FastHTML & HTMX).
- **Git Integration**: Analyze code across commit history
- **Configurable Grading**: Define custom thresholds and scoring for all metrics
- **Multi-Level Reporting**: Summary, directory, file, detailed, derived, and historical views

## Tools & Metrics

### CLOC (Count Lines of Code)
- Lines of code, blank lines, comment lines
- Code density percentage
- Comment ratio
- File size distribution

### Ruff (Python Linting)
- Violation counts per rule and severity
- Violations per KLOC
- Weighted scoring by severity
- Per-file and directory aggregation

### Radon (Complexity Analysis)
Four sub-analyses providing comprehensive complexity metrics:
- **CC** (Cyclomatic Complexity): Function and class complexity
- **MI** (Maintainability Index): Overall maintainability score (0-100)
- **HAL** (Halstead Metrics): Effort, difficulty, bugs prediction
- **RAW** (Raw Metrics): Operators, operands, basic counts

### FXTD (Custom Annotation Tracker)
Track code annotations and technical debt markers:
- FIXME, TODO, HACK, BUG, XXX, NOTE markers
- Weighted scoring by severity
- Per-KLOC metrics

## Installation

### Prerequisites

- Python >= 3.11.9
- External tools (installed separately):
  - `cloc`  - Count Lines of Code
  - `ruff`  - Python linter
  - `radon` - Complexity analyzer
  - `git`   - Version control (for history analysis)

### Install QYX

```bash
# Clone the repository
git clone <repository-url>
cd python-code-quality

# Install with uv (recommended)
uv sync

# The qyx command will be available
qyx --help
```

### Alternative Installation Methods

```bash
# Direct Python invocation
python -m qyx --help

# Using uv run
uv run qyx --help
```

## Quick Start

### Ingest Code Quality Metrics

```bash
# Analyze current project
qyx ingest --name myproject --path /path/to/project

# Analyze with specific tool
qyx ingest --name myproject --path /path/to/project --analysis ruff

# Analyze git history (all commits)
qyx ingest --name myproject --path /path/to/repo

# Read from stdin (pipe tool output)
ruff check --output-format=json . | qyx ingest --name myproject --stdin ruff
```

### View Status

```bash
# Summary status
qyx status

# Grouped by scan
qyx status --level g

# Individual scans
qyx status --level i
```

### Generate Reports

```bash
# Summary report
qyx report --name myproject

# Directory-level report
qyx report --name myproject --level 1

# File-level report
qyx report --name myproject --level 2

# Detailed metrics
qyx report --name myproject --level 3

# Derived metrics (composite scores, rates)
qyx report --name myproject --level d

# Historical trends with charts
qyx report --name myproject --level h
```

### Web Interface

```bash
# Start web server on default port (5011)
qyx serve

# Custom port and auto-launch browser
qyx serve --port 8080 --browser

# Access at http://localhost:5011
```

### Database Administration

```bash
# Safe housekeeping (remove orphaned records)
qyx admin clean

# Remove old scan data
qyx admin trim

# Delete specific project
qyx admin delete

# Complete database wipe (destructive!)
qyx admin clear
```

## Interactive Mode

If you run `qyx` without arguments, it enters interactive mode with guided prompts:

```bash
qyx
# Follow the prompts to select command and options
```

## Configuration

QYX uses `config.yaml` for default settings and metric thresholds.

### Configuration File Location

Default: `./config.yaml` in the project root

### Configuration Structure

```yaml
# Command-line defaults
defaults:
  name: "my-project"
  path: "/path/to/project"
  log_level: "INFO"

# Database configuration
database:
  path: "~/.config/qyx/qyx.sqlite3"

# Tool-specific configurations
tools:
  cloc:
	code_density:
	  thresholds:
		- {min: 10, max: 60, grade: "A", color: "#22c55e"}
		- {min: 60, max: 70, grade: "B", color: "#84cc16"}
		# ... more thresholds

  ruff:
	violation_weights:
	  F: 5.0  # Bugs
	  B: 4.0  # Design
	  S: 4.0  # Security
	  E: 3.0  # Errors
	  # ... more weights

  radon:
	cc:  # Cyclomatic Complexity
	  class_complexity:
		thresholds:
		  - {min: 0, max: 10, grade: "A", color: "#22c55e"}
		  # ... more thresholds

	mi:  # Maintainability Index
	  maintainability_index:
		thresholds:
		  - {min: 85, max: 100, grade: "A", color: "#22c55e"}
		  # ... more thresholds

	hal:  # Halstead Metrics
	  composite:
		thresholds:
		  - {min: 0, max: 50, grade: "A", color: "#22c55e"}
		  # ... more thresholds

  fxtd:
	weights:
	  BUG: 3.0
	  FIXME: 3.0
	  HACK: 3.0
	  TODO: 2.0
	  NOTE: 1.0
```

### Overriding Configuration

CLI arguments override config file settings:

```bash
# Override log level
qyx report --name myproject --log-level DEBUG

# Override project path
qyx ingest --name myproject --path /custom/path
```

## CLI Reference

### Commands

#### `qyx ingest`

Analyze code with quality tools and store results.

```bash
qyx ingest [OPTIONS]
```

**Options:**
- `--name TEXT`: Project name (required)
- `--path PATH`: Project path (required for non-stdin)
- `--analysis TEXT`: Specific analysis to run (cloc, ruff, radon_cc, radon_mi, radon_hal, radon_raw, fxtd)
- `--stdin TEXT`: Read from stdin for specified tool
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

#### `qyx report`

Generate code quality reports.

```bash
qyx report [OPTIONS]
```

**Options:**
- `--name TEXT`: Project name (required)
- `--level LEVEL`: Report level (0=summary, 1=directory, 2=file, 3=detail, d=derived, h=history)
- `--log-level LEVEL`: Logging level

#### `qyx status`

Display project analysis status.

```bash
qyx status [OPTIONS]
```

**Options:**
- `--name TEXT`: Project name (optional, shows all if not specified)
- `--level LEVEL`: Status level (g=grouped, i=individual)
- `--log-level LEVEL`: Logging level

#### `qyx serve`

Start web dashboard server.

```bash
qyx serve [OPTIONS]
```

**Options:**
- `--port INT`: Server port (default: 5011)
- `--browser`: Auto-launch browser
- `--log-level LEVEL`: Logging level

#### `qyx admin clean`

Safe database housekeeping (removes orphaned records).

#### `qyx admin clear`

**DESTRUCTIVE**: Completely wipe database.

#### `qyx admin delete`

Delete specific project from database.

#### `qyx admin trim`

Remove old scan data based on retention policy.

## Web Interface

The web dashboard provides an interactive view of all metrics.

### Features

- **Project Selection**: Dropdown to switch between analyzed projects
- **Tool Panels**: Dedicated panels for each analysis tool (CLOC, Ruff, Radon, FXTD)
- **Dynamic Updates**: HTMX-powered updates without page reloads
- **Charts**: Historical trend visualization using Plotly
- **Multi-Level Views**: Summary, directory, file, and detail levels
- **Health Monitoring**: `/health` endpoint for status checks

### Routes

- `/` - Home dashboard with all tool panels
- `/<tool>` - Detailed view for specific tool
- `/partials/project-selector` - Dynamic project selection
- `/partials/analysis-selector` - Dynamic analysis selection
- `/static/*` - CSS and static assets
- `/health` - Server health check

## Project Structure

```
python-code-quality/
├── src/qyx/                     # Main package
│   ├── __main__.py             # Entry point
│   ├── constants.py            # Enums and constants
│   ├── cli/                    # CLI interface
│   │   ├── ingest.py
│   │   ├── report.py
│   │   ├── status.py
│   │   └── admin/              # Admin commands
│   ├── setup/                  # Configuration & initialization
│   │   ├── args_cli.py
│   │   ├── args_configuration.py
│   │   ├── args_interactive.py
│   │   ├── sqlite.py
│   │   └── tools.py
│   ├── tools/                  # Analysis tool integrations
│   │   ├── base.py             # Base classes
│   │   ├── cloc/
│   │   ├── ruff/
│   │   ├── radon/
│   │   └── fxtd/
│   ├── web/                    # Web interface
│   │   ├── serve.py
│   │   ├── routes.py
│   │   ├── home.py
│   │   └── static/
│   └── utils/                  # Shared utilities
│       ├── git.py
│       ├── scoring.py
│       └── state.py
├── tests/                      # Test suite
├── config.yaml                 # Configuration
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

## Development

### Dependencies

**Core:**
- peewee >= 3.18.3 (ORM)
- python-fasthtml >= 0.12.36 (Web framework)
- plotly >= 6.5.0 (Charts)
- questionary >= 2.1.1 (Interactive prompts)
- rich >= 14.2.0 (Terminal formatting)

**Development:**
- pytest >= 9.0.2 (Testing)

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_smoke_cli.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=qyx
```

### Adding a New Tool

1. Create tool directory in `src/qyx/tools/<tool_name>/`
2. Implement required modules:
   - `__init__.py` - Tool configuration
   - `models.py` - Database models
   - `ingest.py` - Data ingestion logic
   - `cli.py` - CLI rendering (if desired)
   - `web.py` - Web rendering (if desired but at least one rendering is suggested)
3. Add requisite/desired configuration to `config.yaml`

### Tool Implementation Pattern

Each tool follows a standard pattern:

```python
# __init__.py - Tool configuration
class MyToolConfiguration(AbstractToolConfiguration):
	tool_name = "mytool"
	command = "mytool --json {path}"
	report_levels = [0, 1, 2]  # Supported report levels

# models.py - Data models
class MyToolResult(BaseResultsModel):
	# Define fields
	pass

# ingest.py - Data ingestion
def ingest(scan: Scan, data: dict) -> None:
	# Parse and store data
	pass

# cli.py - CLI rendering
def render_cli(scan: Scan, level: int) -> None:
	# Render to terminal
	pass

# web.py - Web rendering
def render_web(scan: Scan, level: int) -> FT:
	# Render to FastHTML
	pass
```

### Database Schema

QYX uses Peewee ORM with SQLite3.

**Core Tables:**
- `project` - Project records
- `request` - Analysis requests
- `scan` - Individual tool runs

**Tool-Specific Tables:**
- `cloc` - Line counting
- `ruff` - Linting violations
- `radon_cc` - Cyclomatic complexity
- `radon_mi` - Maintainability index
- `radon_hal` - Halstead metrics
- `radon_hal_function` - Per-function Halstead
- `radon_raw` - Raw metrics
- `fxtd` - Annotation tracking

### Poe Tasks

Quick automation tasks defined in `pyproject.toml`:

```bash
# Deploy (clean, update, push)
poe deploy

# Run QYX
poe qyx

# Start server
poe serve

# Report status
poe status

# Generate report
poe report

# Database operations
poe clean
poe clear

# Open database in litecli
poe sql
```

## Grading System

QYX uses a configurable grading system (A-F) with color coding:

- **A** (Green): Excellent
- **B** (Light Green): Good
- **C** (Yellow): Acceptable
- **D** (Orange): Needs Improvement
- **F** (Red): Poor

Each metric has customizable thresholds in `config.yaml`:

```yaml
thresholds:
  - {min: 85, max: 100, grade: "A", color: "#22c55e"}
  - {min: 70, max: 85, grade: "B", color: "#84cc16"}
  - {min: 60, max: 70, grade: "C", color: "#eab308"}
  - {min: 50, max: 60, grade: "D", color: "#f97316"}
  - {min: 0, max: 50, grade: "F", color: "#ef4444"}
```

## Report Levels

QYX provides multiple reporting levels for different perspectives:

| Level | Name      | Description                                            |
|-------|-----------|--------------------------------------------------------|
| 0     | Summary   | Project-level overview with overall metrics            |
| 1     | Directory | Directory-level aggregation                            |
| 2     | File      | File-level detail                                      |
| 3     | Detail    | Deep detailed metrics (function-level where available) |
| d     | Derived   | Composite scores, rates of change, trends              |
| h     | History   | Historical trends with charts                          |

## Examples

### Typical Workflow

```bash
# 1. Initial analysis
qyx ingest --name myproject --path ~/projects/myapp

# 2. Check status
qyx status --name myproject

# 3. View summary report
qyx report --name myproject --level 0

# 4. Drill into files with issues
qyx report --name myproject --level 2

# 5. Start web dashboard for exploration
qyx serve --browser

# 6. After code changes, re-analyze
qyx ingest --name myproject --path ~/projects/myapp

# 7. View historical trends
qyx report --name myproject --level h
```

### Analyzing Git History

```bash
# Analyze all commits in repository
qyx ingest --name myproject --path https://github.org/someone/myproject

# This will:
# 1. Clone the repo and get the complete commit history
# 2. For each commit not yet processed:
# 3. - Will checkout the commit
# 4. - Run analysis tools
# 5. - Store results with commit metadata

# View historical trends
qyx report --name myproject --level h
```

### Custom Analysis Pipeline

```bash
# Run only specific tools
qyx ingest --name myproject --path . --analysis ruff
qyx ingest --name myproject --path . --analysis radon_cc

# Pipe custom tool output
my-custom-tool --json | qyx ingest --name myproject --stdin ruff
```

## Troubleshooting

### Database Issues

```bash
# Clean up orphaned records
qyx admin clean

# Reset database completely
qyx admin clear
```

### Tool Not Found

Ensure external tools are installed:

```bash
# Check if tools are available
which cloc
which ruff
which radon

# Install missing tools
pip install ruff radon
# Install cloc via package manager (brew, apt, etc.)
```

### Permission Issues

Database location: `~/.config/qyx/qyx.sqlite3`

Ensure write permissions:

```bash
mkdir  -p ~/.config/qyx
chmod 755 ~/.config/qyx
```

## Contributing

This is a proof-of-concept project. Contributions are welcome!

### Areas for Enhancement

- Additional tool integrations (pylint, mypy, bandit, etc.)
- Export functionality (PDF reports, CSV data)
- Comparison views (branch comparison, before/after)
- Alerting and thresholds
- CI/CD integration
- Docker containerization
- Multi-language support

## License

[Add your license here]

## Author

Peter Borocz

## Acknowledgments

Built with:
- [Peewee](http://docs.peewee-orm.com/) - Simple and expressive ORM
- [FastHTML](https://fastht.ml/) - Modern Python web framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [HTMX](https://htmx.org/) - Dynamic web interactions
- [Plotly](https://plotly.com/python/) - Elegant charts

## Version

0.1.0 (POC)
