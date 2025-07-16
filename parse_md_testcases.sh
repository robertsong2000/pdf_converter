#!/bin/bash
set -Eeuo pipefail

for i in *DVM*.md; do
    echo "Processing file: $i"
    dirname=$(echo $i|sed -e 's/.md//')
    mkdir -p testcases_$dirname
    python3 "$(dirname "$0")/md_testcase_parser.py" -o testcases_$dirname "$i"
    cp "$i" "$(dirname "$i")/testcases_$dirname/"
done

for dir in testcases_*; do
    if [ -d "$dir" ]; then
        zip -r "$dir.zip" "$dir"
    fi
done