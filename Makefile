# Top-level Makefile for the doc-chat demo monorepo. Run from the repo root.

.PHONY: install up down test format pr-check api-test website-test cdk-test cdk-synth clean

install:
	@echo "Installing Python (uv) and Node (npm) deps..."
	cd packages/api && uv sync --extra dev
	cd packages/website && npm install
	cd packages/cdk && npm install

up:
	@if [ -z "$$DOCUMENTS_BUCKET" ]; then \
	  echo "DOCUMENTS_BUCKET not set — fetching from CloudFormation..."; \
	  DOCUMENTS_BUCKET=$$(aws cloudformation describe-stacks \
	    --stack-name DocChatDevResources \
	    --query 'Stacks[0].Outputs[?OutputKey==`DocumentsBucketName`].OutputValue' \
	    --output text 2>/dev/null); \
	  if [ -z "$$DOCUMENTS_BUCKET" ]; then \
	    echo "Could not fetch from CFN. Export it manually:"; \
	    echo "  export DOCUMENTS_BUCKET=demo-doc-chat-documents-\$$(aws sts get-caller-identity --query Account --output text)"; \
	    exit 1; \
	  fi; \
	  export DOCUMENTS_BUCKET; \
	  echo "  Using DOCUMENTS_BUCKET=$$DOCUMENTS_BUCKET"; \
	fi; \
	CREDS=$$(aws configure export-credentials --format env 2>/dev/null | sed 's/^export //'); \
	if [ -z "$$CREDS" ]; then \
	  echo "WARNING: Could not extract AWS credentials (SSO expired?). AWS calls may fail."; \
	  DOCUMENTS_BUCKET=$${DOCUMENTS_BUCKET} docker compose up -d --build; \
	else \
	  env $$CREDS DOCUMENTS_BUCKET=$${DOCUMENTS_BUCKET} docker compose up -d --build; \
	fi
	@echo ""
	@echo "API:  http://localhost:8000  (healthz: http://localhost:8000/healthz)"
	@echo "Web:  http://localhost:3000"
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
	cd packages/cdk && \
	  WORKSPACE_IRSA_ROLE_ARN=$${WORKSPACE_IRSA_ROLE_ARN:-arn:aws:iam::111111111111:role/workspace-irsa-role} \
	  CDK_DEFAULT_ACCOUNT=$${CDK_DEFAULT_ACCOUNT:-111111111111} \
	  CDK_DEFAULT_REGION=$${CDK_DEFAULT_REGION:-us-east-1} \
	  npx cdk synth > /dev/null

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
