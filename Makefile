PY := .venv/bin/python

.DEFAULT_GOAL := help
.PHONY: help setup test lint

help: ## list commands
	@grep -hE '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-6s %s\n", $$1, $$2}'

setup: ## create .venv, install the project, create .env
	python3 -m venv .venv
	$(PY) -m pip install -q -e ".[dev]"
	@test -f .env || cp .env.example .env

test: ## offline unit tests (no key, no network)
	$(PY) -m pytest tests/unit -q

lint: ## ruff check
	$(PY) -m ruff check src tests
