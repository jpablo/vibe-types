# Central command runner for vibe-types.
# Run `make` (or `make help`) to list targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

PY_PROJECT := projects/python-project
VERIFY     := plugin/skills/verify-markdown-snippets/scripts/verify_markdown.py

.PHONY: help setup verify tenets-check test check clean

help: ## List available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install the Python reference project deps (needed for snippet verification)
	cd $(PY_PROJECT) && uv sync

verify: ## Verify code snippets in a markdown file: make verify FILE=path/to.md [MATCH=1]
	@if [ -z "$(FILE)" ]; then echo "usage: make verify FILE=<markdown file> [MATCH=1]"; exit 2; fi; \
	python3 $(VERIFY) "$(FILE)" $(if $(MATCH),--match-errors,)

tenets-check: ## Check that each skill's Core tenets still match docs/core-tenets.md
	@fail=0; \
	for lang in scala3 rust python lean; do \
		if diff -q \
			<(awk '/^## Core tenets/{f=1;next} /^## Full catalog/{f=0} f' plugin/skills/$$lang/SKILL.md | sed -E 's/ → .*$$//') \
			<(awk '/^---$$/{f=1;next} f' docs/core-tenets.md) >/dev/null; then \
			echo "  ok    $$lang"; \
		else \
			echo "  DRIFT $$lang"; fail=1; \
		fi; \
	done; \
	if [ $$fail -ne 0 ]; then \
		echo "tenets out of sync: edit docs/core-tenets.md, then propagate the wording to the skills"; \
		exit 1; \
	fi; \
	echo "all skills match docs/core-tenets.md"

test: ## Run the snippet-extractor unit tests
	cd plugin/skills/verify-markdown-snippets/scripts && uv run --with pytest pytest -q

check: tenets-check test ## Run the fast, dependency-light checks (tenets sync + extractor tests)

clean: ## Remove caches and generated snippet reports
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(PY_PROJECT)/reports
