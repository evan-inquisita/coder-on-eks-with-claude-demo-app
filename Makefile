# Top-level Makefile for the doc-chat demo monorepo. Run from the repo root.

.PHONY: install up down test format pr-check api-test website-test cdk-test cdk-synth clean

install:
	@echo "Installing Python (uv) and Node (npm) deps..."
	cd packages/api && uv sync --extra dev
	cd packages/website && npm install
	cd packages/cdk && npm install

up:
	@if [ -z "$$DOCUMENTS_BUCKET" ]; then \
	  echo "DOCUMENTS_BUCKET not set. Export it before 'make up'."; \
	  echo "  export DOCUMENTS_BUCKET=doc-chat-documents-\$$(aws sts get-caller-identity --query Account --output text)"; \
	  exit 1; \
	fi
	docker compose up -d --build
	@echo ""
	@echo "API:  http://localhost:8000  (healthz: http://localhost:8000/healthz)"
	@echo "Web:  http://localhost:5173"
	@echo ""
	@echo "Inside a Coder workspace, use the preview-urls skill to get the public URLs."

down:
	docker compose down

api-test:
	cd packages/api && uv run pytest -v

website-test:
	cd packages/website && npm test

cdk-test:
	cd packages/cdk && npm test

cdk-synth:
	cd packages/cdk && npx cdk synth > /dev/null

test: api-test website-test cdk-test

format:
	cd packages/api && uv run ruff format .
	cd packages/website && npm run format

pr-check: format test cdk-synth
	@echo "OK pr-check"

clean:
	docker compose down -v
	rm -rf packages/api/.pytest_cache packages/api/.ruff_cache
	rm -rf packages/cdk/cdk.out
