# Multi-stage build. The first stage installs deps with uv into a virtualenv,
# the second stage copies the venv into a slim runtime image. The same image
# is what a production CDK would push to ECR and run on Fargate — locally
# we run it via docker-compose.

# ── builder ──
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml ./
COPY doc_chat_api ./doc_chat_api

RUN uv venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python . \
    && uv pip install --python /opt/venv/bin/python "uvicorn[standard]>=0.32"

# ── runtime ──
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Non-root user. Home dir is /home/api so the docker-compose bind-mount of
# the workspace's ~/.aws lands in the right place for boto3 credential lookup.
RUN useradd -m -u 1000 -s /bin/bash api
WORKDIR /home/api/app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=api:api doc_chat_api ./doc_chat_api

USER api

EXPOSE 8000
CMD ["uvicorn", "doc_chat_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
