SHELL = bash
.DEFAULT_GOAL := help
.PHONY: help

help:  ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-42s\033[0m %s\n", $$1, $$2}'

ci--github--tag-is-latest-tag:  ## Github Actions only: Checks that the tag checked out in this Action is the latest tag in the repo
	@bash scripts/github_tag_is_latest_tag.sh

ci--version-equals-latest-tag: ## Verify that the version in pyproject.toml is the same as the latest tag in the repo.
	@bash scripts/version_equals_latest_tag.sh

ci--version-greater-than-latest-tag:  ## Verify that the version in pyproject.toml is semantically greater than the latest tag in the repo.
	@bash scripts/version_greater_than_latest_tag.sh

test--unit: ## Run unit tests
	poetry run python -m pytest -m 'not integration' --suppress-no-test-exit-code $(PYTEST_FLAGS)

test--integration:  ## Run integration tests
	poetry run python -m pytest -m 'integration' --suppress-no-test-exit-code $(PYTEST_FLAGS)

test--integration--from-build: pkg--build ## Run integration tests from the build without poetry
	@bash scripts/integration_tests_from_build.sh

pkg--build: pkg--clean ## Build a package that could be published
	poetry build

pkg--clean: ## Remove previous builds
	[ -d dist ] && rm -rf dist || :

pkg--helpers--latest-tag: ## Print the latest tag in this repo
	git tag -l --sort -version:refname | head -n 1

pkg--helpers--increment-version--patch: ## Increments the package PATCH version
	poetry version patch

pkg--helpers--increment-version--minor: ## Increments the package PATCH version
	poetry version minor

pkg--helpers--create-release-from-version: ci--version-greater-than-latest-tag ## Creates a new tag and sets it to
	@bash scripts/create_release.sh


lint:  ## Lint / fix all files
	.venv/bin/pre-commit run --all-files

venv--update:  ## Updates installed dependencies as specified in pyproject.toml
	poetry update

venv--install:  ## First time installation of poetry configuration
	poetry || (pip install --upgrade pip && pip install poetry)
	poetry config virtualenvs.in-project true
	poetry install --with dev --no-ansi
	.venv/bin/pre-commit install
