.PHONY: test test-unit test-integration test-e2e test-cov lint format format-check lock-check audit pre-commit security doctor check

TEST_APP_ENV ?= test
PYTEST = APP_ENV=$(TEST_APP_ENV) poetry run pytest

test:
	$(PYTEST) tests/ -v

test-unit:
	$(PYTEST) tests/ -v -m unit

test-integration:
	$(PYTEST) tests/ -v -m integration

test-e2e:
	$(PYTEST) tests/ -v -m e2e

test-cov:
	$(PYTEST) tests/ -v --cov --cov-report=term-missing --cov-report=html --cov-fail-under=85

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

format-check:
	poetry run ruff format --check .

lock-check:
	poetry check --lock

audit:
	poetry run pip-audit --progress-spinner off

pre-commit:
	poetry run pre-commit run --all-files --show-diff-on-failure

security: lock-check audit pre-commit

doctor:
	poetry run python -m scripts.doctor

check: lock-check lint format-check test
