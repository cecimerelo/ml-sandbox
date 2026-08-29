# One command per thing you actually want to do.
#
# The frontend proxies /api to the backend (see app/vite.config.ts), so both halves are
# same-origin in the browser: nothing needs CORS, and no base URL is configured per
# environment — one fewer thing to differ between dev and deploy.

.PHONY: dev api web test lint

dev:  ## Run both halves. Backend on :8000, frontend on :5173.
	@echo "backend  http://127.0.0.1:8000/api/health"
	@echo "frontend http://localhost:5173"
	@$(MAKE) -j2 api web

api:
	uv run uvicorn mlsandbox.api:app --reload --port 8000

web:
	cd app && npm run dev

test:
	uv run pytest -q
	cd app && npm test

lint:
	uv run ruff check .
	cd app && npm run lint
