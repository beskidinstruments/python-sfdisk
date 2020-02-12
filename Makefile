# The binary to build (just the basename).
MODULE := pysfdisk

# This version-strategy uses git tags to set the version string
TAG := $(shell git describe --tags --always --dirty)

BLUE='\033[0;34m'
NC='\033[0m' # No Color

run:
	@python -m $(MODULE)

test:
	@pytest

lint:
	@echo "\n${BLUE}Applying isort...${NC}\n"
	@isort apply **/*.py
	@echo "\n${BLUE}Reformat code via black...${NC}\n"
	@black -l 120 **/*.py
	@echo "\n${BLUE}Reformat docstrings via docformatter...${NC}\n"
	@docformatter --in-place --blank --pre-summary-newline **/*.py
	@echo "\n${BLUE}Running Pylint against source and test files...${NC}\n"
	@pylint --rcfile=setup.cfg **/*.py
	@echo "\n${BLUE}Running Flake8 against source and test files...${NC}\n"
	@flake8
	@echo "\n${BLUE}Running Bandit against source files...${NC}\n"
	@bandit -r --ini setup.cfg **/*.py


version:
	@echo $(TAG)

.PHONY: clean test

clean:
	rm -rf .pytest_cache .coverage .pytest_cache coverage.xml
