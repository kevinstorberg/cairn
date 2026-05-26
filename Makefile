.PHONY: test test-unit test-integration test-e2e lint format check

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/ -v -m unit

test-integration:
	poetry run pytest tests/ -v -m integration

test-e2e:
	poetry run pytest tests/ -v -m e2e

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

check: lint test
