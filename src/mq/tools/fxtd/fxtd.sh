#!/bin/bash

set -euo pipefail

# Use ${1:-.} to accept directory as argument, default to current dir
TARGET_DIR="${1:-.}"

# Find all .py/.js files, excluding hidden directories (those starting with .)
find "$TARGET_DIR" -type d -name ".*" -prune -o -type f \( -name "*.py" -o -name "*.js" \) -print0 | \

    xargs -0 grep -in "# \(FIXME\|TODO\|HACK\|XXX\)" | \

    while IFS=: read -r file line_number line_content; do

	if echo "$line_content" | grep -q "# FIXME"; then
	    echo "FIXME|$file|$line_number|$line_content"

	elif echo "$line_content" | grep -q "# TODO"; then
	    echo "TODO|$file|$line_number|$line_content"

	fi
    done
