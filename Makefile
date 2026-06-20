# Central command runner for vibe-types.
# Run `make` (or `make help`) to list targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

PY_PROJECT  := projects/python-project
TS_PROJECT  := projects/typescript-project
VERIFY      := plugin/skills/verify-markdown-snippets/scripts/verify_markdown.py
VERIFY_DOCS := bash plugin/skills/verify-markdown-snippets/scripts/verify_docs.sh

.PHONY: help setup verify verify-python verify-rust verify-scala verify-typescript verify-lean tenets-check test check clean

help: ## List available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install reference-project deps used by the snippet checkers (Python venv + TypeScript compiler)
	cd $(PY_PROJECT) && uv sync
	cd $(TS_PROJECT) && npm install

verify: ## Verify code snippets in one markdown file: make verify FILE=path/to.md [MATCH=1]
	@if [ -z "$(FILE)" ]; then echo "usage: make verify FILE=<markdown file> [MATCH=1]"; exit 2; fi; \
	python3 $(VERIFY) "$(FILE)" $(if $(MATCH),--match-errors,)

verify-python: ## Verify every Python doc snippet (catalog + usecases): make verify-python [MATCH=1]
	@$(VERIFY_DOCS) python python-project $(if $(MATCH),--match-errors,)

verify-rust: ## Verify every Rust doc snippet (slow; first run builds deps): make verify-rust [MATCH=1]
	@$(VERIFY_DOCS) rust rust-project $(if $(MATCH),--match-errors,)

verify-scala: ## Verify every Scala doc snippet (slow; first run fetches the compiler): make verify-scala [MATCH=1]
	@$(VERIFY_DOCS) scala3 scala-project $(if $(MATCH),--match-errors,)

verify-typescript: ## Verify every TypeScript doc snippet (run `make setup` first): make verify-typescript [MATCH=1]
	@$(VERIFY_DOCS) typescript typescript-project $(if $(MATCH),--match-errors,)

verify-lean: ## Verify every Lean doc snippet (needs the Lean toolchain via elan): make verify-lean [MATCH=1]
	@$(VERIFY_DOCS) lean lean-project $(if $(MATCH),--match-errors,)

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
