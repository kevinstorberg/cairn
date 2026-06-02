.PHONY: test test-unit test-integration test-e2e test-cov lint format format-check lock-check audit pre-commit security doctor check

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/ -v -m unit

test-integration:
	poetry run pytest tests/ -v -m integration

test-e2e:
	poetry run pytest tests/ -v -m e2e

test-cov:
	poetry run pytest tests/ -v --cov --cov-report=term-missing --cov-report=html --cov-fail-under=85

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
