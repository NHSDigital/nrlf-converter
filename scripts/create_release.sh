#!/bin/bash

set -e
POETRY_VERSION=$(poetry version | rev | cut -d ' ' -f 1 | rev)
git tag ${POETRY_VERSION}
git push origin --tags
