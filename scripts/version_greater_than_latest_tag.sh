#!/bin/bash

POETRY_VERSION=$(poetry version | rev | cut -d ' ' -f 1 | rev)
MAX_TAG=$(git tag -l --sort -version:refname | head -n 1)

function version {
    # Lifted from https://stackoverflow.com/a/37939589/1571593
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }';
}

if [ $(version $POETRY_VERSION) -le $(version $MAX_TAG) ]; then
    echo "ERROR: poetry version '${POETRY_VERSION}' must be greater than latest tag '${MAX_TAG}'"
    exit 1;
fi
