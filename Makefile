.PHONY: help setup run-backend run-frontend test lint

help:
	@echo "Available commands:"
	@echo "  make setup        - Set up the development environment"
	@echo "  make run-backend  - Run the backend server"
	@echo "  make run-frontend - Run the frontend server"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"

setup:
	cd backend && python -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install

run-backend:
	cd backend && . venv/bin/activate && \
		uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm start

test:
	cd backend && . venv/bin/activate && pytest
	cd frontend && npm test

lint:
	cd backend && . venv/bin/activate && \
		black . && \
		flake8 . && \
		mypy .
	cd frontend && npm run lint

docker-up:
	docker-compose -f infrastructure/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infrastructure/docker/docker-compose.yml down