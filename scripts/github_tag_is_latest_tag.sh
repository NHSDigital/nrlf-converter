#!/bin/bash
MAX_TAG=$(git tag -l --sort -version:refname | head -n 1)
if [ "${GITHUB_REF_NAME}" != "${MAX_TAG}" ]; then
    echo "ERROR: Current tag '${GITHUB_REF_NAME}' does not match latest tag '${MAX_TAG}'"
    exit 1
fi
