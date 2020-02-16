# The binary to build (just the basename).
MODULE := pysfdisk

# This version-strategy uses git tags to set the version string
TAG := $(shell git describe --tags --always --dirty)

BLUE='\033[0;34m'
NC='\033[0m' # No Color

# https://postd.cc/auto-documented-makefile/
help: ## Show help
	@grep --no-filename -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

run:
	@python -m $(MODULE)

test: ## Run test via pytest
	@pytest

lint: ## Lint your code and reformat it using black, docstrings, isort and others
	@echo "\n${BLUE}Applying isort...${NC}\n"
	@isort apply **/*.py
	@echo "\n{BLUE}Reformat code via black...${NC}\n"
	@black -l 120 **/*.py
	@echo "\n${BLUE}Reformat docstrings via docformatter...${NC}\n"
	@docformatter --in-place --blank --pre-summary-newline --wrap-summaries 120 --wrap-descriptions 120 **/*.py
	@echo "\n${BLUE}Running Pylint against source and test files...${NC}\n"
	@pylint --rcfile=setup.cfg **/*.py
	@echo "\n${BLUE}Running Flake8 against source and test files...${NC}\n"
	@flake8
	@echo "\n${BLUE}Running Bandit against source files...${NC}\n"
	@bandit -r --ini setup.cfg

dependencies: ## List dependencies used in project
	@echo "\n{BLUE}Show module dependencies ${NC}\n"
	@pipdeptree

version: ## Show git tag
	@echo $(TAG)

.PHONY: clean test

clean: ## Remove pytest and coverage artifacts
	rm -rf .pytest_cache .coverage .pytest_cache coverage.xml
