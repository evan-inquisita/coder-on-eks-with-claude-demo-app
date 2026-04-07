-- packages/api/doc_chat_api/migrations/001_initial.sql
--
-- Single migration for the demo. Applied by Postgres at first boot via the
-- docker-entrypoint-initdb.d mechanism (see docker-compose.yml). Production
-- would use a migration tool (Alembic, sqlx, etc.) — for a single-table
-- demo this is overkill.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    s3_key      TEXT NOT NULL UNIQUE,
    size_bytes  BIGINT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_doc_created ON messages(document_id, created_at);
