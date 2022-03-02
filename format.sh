#!/usr/bin/env bash

function main() {
    # The directory to work on is either passed in as argument 1,
    # or is the current working directory
    DIRECTORY=${1:-`pwd`}
    LINE_LENGTH=88

    isort \
      --overwrite-in-place \
      --profile black \
      -j `nproc` \
      --line-length $LINE_LENGTH \
      --python-version auto \
      $DIRECTORY

    black \
      --line-length $LINE_LENGTH \
      --required-version 22.1.0 \
      --target-version py38 \
      --safe \
      $DIRECTORY
}

function help() {
  echo "usage: format.sh <directory>"
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  help
  exit 0
fi

main "$1"

