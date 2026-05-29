.PHONY: test test-unit test-integration test-e2e test-cov lint format format-check check

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/ -v -m unit

test-integration:
	poetry run pytest tests/ -v -m integration

test-e2e:
	poetry run pytest tests/ -v -m e2e

test-cov:
	poetry run pytest tests/ -v --cov --cov-report=term-missing --cov-report=html

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

format-check:
	poetry run ruff format --check .

check: lint format-check test
