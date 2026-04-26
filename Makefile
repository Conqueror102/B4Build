.PHONY: help install dev backend frontend test lint fmt clean

help:
	@echo "AI Build Advisor - common tasks"
	@echo ""
	@echo "  make install   Install backend (uv) and frontend (pnpm) deps"
	@echo "  make dev       Run backend and frontend in parallel (requires concurrent terminals)"
	@echo "  make backend   Run backend dev server"
	@echo "  make frontend  Run frontend dev server"
	@echo "  make test      Run backend pytest + frontend vitest"
	@echo "  make lint      Run ruff + mypy + eslint"
	@echo "  make fmt       Auto-format Python (ruff) and TS (prettier)"
	@echo "  make clean     Remove caches and build artifacts"

install:
	cd backend && uv sync
	cd frontend && pnpm install

backend:
	cd backend && uv run uvicorn src.main:app --reload --port 8000

frontend:
	cd frontend && pnpm dev

test:
	cd backend && uv run pytest
	cd frontend && pnpm test

lint:
	cd backend && uv run ruff check . && uv run mypy src
	cd frontend && pnpm lint && pnpm typecheck

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && pnpm format

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
