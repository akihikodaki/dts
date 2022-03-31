#!/usr/bin/env bash

./format.sh

if [ -n "$(git diff --shortstat)" ]; then
    echo "Formatting: FAIL"
    echo "Improperly formatted files found, run <dts root>/format.sh and re-submit your patch."
    git diff --stat
    exit 1
else
    echo "Formatting: PASS"
    exit 0
fi