#!/bin/bash

set -euo pipefail

# Use ${1:-.} to accept directory as argument, default to current dir
TARGET_DIR="${1:-.}"

KEYWORD_PATTERN="BUG\|FIXME\|HACK\|IDEA\|NOTE\|OPTIMIZE\|REFACTOR\|TODO\|XXX"

# Find all .py/.js files, excluding hidden directories (those starting with .)
find "$TARGET_DIR" -type d -name ".*" -prune -o -type f \( -name "*.py" -o -name "*.js" \) -print0 | \
    xargs -0 grep -iEn "# ($KEYWORD_PATTERN)" | \
    while IFS=: read -r file line_number line_content; do
	keyword=$(echo "$line_content" | grep -oE "# ($KEYWORD_PATTERN)" | sed 's/# //')
	echo "$keyword|$file|$line_number|$line_content"
    done
