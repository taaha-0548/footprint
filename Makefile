export PYTHONHASHSEED := 0
PY := uv run python

.PHONY: setup test lint env data split resolve extract tasks index predict eval pilot test-eval

setup:
	uv sync
	$(MAKE) env

test:
	uv run pytest -q

lint:
	uv run ruff check src tests scripts

env:
	$(PY) scripts/record_env.py

# Pipeline stages are added milestone by milestone (M1 onward).
data split resolve extract tasks index predict eval pilot:
	@echo "'$@' is not implemented yet (see PRD Section 6)"; exit 1

# Guarded: test split is touched only after explicit human approval (Rule 3).
test-eval:
	@test "$(CONFIRM)" = "yes" || { echo "Refusing: run 'make test-eval CONFIRM=yes' only after human approval"; exit 1; }
	@echo "'test-eval' is not implemented yet (M11)"; exit 1
