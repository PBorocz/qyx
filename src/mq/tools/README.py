"""
Report Module Naming Convention
================================
Files follow the pattern: {metric}_{level}.py

Metrics: cc, hal, mi, raw
Levels: 0, 1, 2, 3, d, h
Example: cc_0.py = Cyclomatic Complexity, Level 0 (Summary)

Each module must export a `generate_report()` function with signature:
def generate_report(scan: Scan, config: dict) -> str:
   ...

The CLI dynamically imports based on user's --level argument.
"""
