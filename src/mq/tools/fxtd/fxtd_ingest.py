"""..."""

import os
import re
import sys
from pathlib import Path


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    keywords = ["BUG", "FIXME", "HACK", "IDEA", "NOTE", "OPTIMIZE", "REFACTOR", "TODO", "XXX"]
    pattern = re.compile(r"#\s*(" + "|".join(keywords) + r")", re.IGNORECASE)

    # Walk through directory
    for root, dirs, files in os.walk(target_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if not (file.endswith(".py") or file.endswith(".js")):
                continue

            filepath = Path(root) / file

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_number, line in enumerate(f, start=1):
                        match = pattern.search(line)
                        if match:
                            keyword = match.group(1).upper()
                            line_content = line.rstrip("\n")
                            print(f"{keyword}|{filepath}|{line_number}|{line_content}")
            except Exception:
                # Skip files that can't be read
                pass


if __name__ == "__main__":
    main()
