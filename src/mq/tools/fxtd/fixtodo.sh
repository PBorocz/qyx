#!/bin/bash

set -euo pipefail

# Check if directory argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <root_directory>" >&2
    exit 1
fi

ROOT_DIR="$1"

# Check if directory exists
if [ ! -d "$ROOT_DIR" ]; then
    echo "Error: Directory '$ROOT_DIR' does not exist" >&2
    exit 1
fi

# Find all .py files, excluding hidden directories, and search with grep
find "$ROOT_DIR" -name ".*" -prune -o -type f \( -name "*.py" -o -name "*.js" \) -print0 | \
    xargs -0 grep -in "# \(FIXME\|TODO\|HACK\|XXX\)" | \
    while IFS=: read -r file line_number line_content; do
	if echo "$line_content" | grep -q "# FIXME"; then
	    echo "FIXME|$file|$line_number|$line_content"
	elif echo "$line_content" | grep -q "# TODO"; then
	    echo "TODO|$file|$line_number|$line_content"
	fi
    done
# #!/bin/bash

# set -euo pipefail

# # Check if directory argument is provided
# if [ $# -eq 0 ]; then
#     echo "Usage: $0 <root_directory>" >&2
#     exit 1
# fi

# ROOT_DIR="$1"

# # Check if directory exists
# if [ ! -d "$ROOT_DIR" ]; then
#     echo "Error: Directory '$ROOT_DIR' does not exist" >&2
#     exit 1
# fi

# # Find all .py files, excluding hidden directories
# while IFS= read -r -d '' file; do
#     line_number=0
#     while IFS= read -r line; do
#	((line_number++))

#	# Check for FIXME
#	if echo "$line" | grep -q "# FIXME"; then
#	    echo "FIXME|$file|$line_number|$line"
#	fi

#	# Check for TODO
#	if echo "$line" | grep -q "# TODO"; then
#	    echo "TODO|$file|$line_number|$line"
#	fi
#     done < "$file"
# done < <(find "$ROOT_DIR" -name ".*" -prune -o -type f -name "*.py" -print0)
