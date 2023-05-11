#!/bin/bash

POETRY_VERSION=$(poetry version | rev | cut -d ' ' -f 1 | rev)
MAX_TAG=$(git tag -l --sort -version:refname | head -n 1)
if [ "${POETRY_VERSION}" != "${MAX_TAG}" ]; then
    echo "ERROR: poetry version '${POETRY_VERSION}' does not match latest tag '${MAX_TAG}'"
    exit 1;
fi
