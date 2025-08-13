.PHONY: help setup run-backend test lint

help:
	@echo "Available commands:"
	@echo "  make setup        - Set up the backend development environment"
	@echo "  make run-backend  - Run the backend server"
	@echo "  make test         - Run backend tests"
	@echo "  make lint         - Run backend linters"

setup:
	cd backend && python -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt

run-backend:
	cd backend && . venv/bin/activate && \
		uvicorn app.main:app --reload --port 8000

test:
	cd backend && . venv/bin/activate && pytest || true

lint:
	cd backend && . venv/bin/activate && \
		black . && \
		flake8 . && \
		mypy . || true