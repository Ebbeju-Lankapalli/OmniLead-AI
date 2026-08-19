SHELL := /bin/bash

FRONTEND_DIR := frontend
BACKEND_DIR := backend

.PHONY: help \
	setup \
	frontend-install \
	backend-install \
	dev \
	frontend-dev \
	backend-dev \
	worker \
	test \
	frontend-test \
	backend-test \
	e2e-test \
	lint \
	frontend-lint \
	backend-lint \
	format \
	frontend-format \
	backend-format \
	typecheck \
	migrate \
	migration \
	seed-demo \
	reset-demo \
	precommit \
	clean

help:
	@echo ""
	@echo "OmniLead AI development commands"
	@echo "--------------------------------"
	@echo "make setup            Install frontend and backend dependencies"
	@echo "make dev              Start the complete local development stack"
	@echo "make frontend-dev     Start the Vite frontend"
	@echo "make backend-dev      Start the FastAPI backend"
	@echo "make worker           Start the Celery worker"
	@echo "make test             Run backend and frontend tests"
	@echo "make e2e-test         Run Playwright end-to-end tests"
	@echo "make lint             Run frontend and backend linting"
	@echo "make format           Format frontend and backend code"
	@echo "make typecheck        Run frontend TypeScript checks"
	@echo "make migrate          Apply Alembic database migrations"
	@echo "make migration        Create a new Alembic migration"
	@echo "make seed-demo        Seed synthetic demo data"
	@echo "make reset-demo       Reset synthetic demo data"
	@echo "make precommit        Run all pre-commit hooks"
	@echo "make clean            Remove generated caches and build artifacts"
	@echo ""

setup: frontend-install backend-install

frontend-install:
	cd $(FRONTEND_DIR) && npm install

backend-install:
	cd $(BACKEND_DIR) && python -m pip install --upgrade pip
	cd $(BACKEND_DIR) && python -m pip install -r requirements.txt

dev:
	./scripts/dev.sh

frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

backend-dev:
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload

worker:
	cd $(BACKEND_DIR) && celery -A app.workers.celery_app.celery_app worker --loglevel=info

test: backend-test frontend-test

backend-test:
	cd $(BACKEND_DIR) && pytest

frontend-test:
	cd $(FRONTEND_DIR) && npm run test

e2e-test:
	cd $(FRONTEND_DIR) && npx playwright test

lint: backend-lint frontend-lint

backend-lint:
	cd $(BACKEND_DIR) && ruff check .

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

format: backend-format frontend-format

backend-format:
	cd $(BACKEND_DIR) && ruff format .
	cd $(BACKEND_DIR) && ruff check . --fix

frontend-format:
	cd $(FRONTEND_DIR) && npm run format

typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

migrate:
	cd $(BACKEND_DIR) && alembic upgrade head

migration:
	@if [ -z "$(m)" ]; then \
		echo "Usage: make migration m=\"migration description\""; \
		exit 1; \
	fi
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(m)"

seed-demo:
	python scripts/seed_demo.py

reset-demo:
	python scripts/reset_demo.py

precommit:
	pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(FRONTEND_DIR)/coverage
	rm -rf playwright-report
	rm -rf test-results