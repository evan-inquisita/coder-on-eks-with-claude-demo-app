"""Documents routes — upload, list, get, delete.

The router reads `app.state.db` and `app.state.s3` so tests can substitute
fakes without monkeypatching imports.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("")
async def upload_document(request: Request, file: UploadFile) -> dict:
    db = request.app.state.db
    s3 = request.app.state.s3

    body = await file.read()
    size_bytes = len(body)
    filename = file.filename or "document.pdf"

    # Reserve an id so the s3 key can include it
    from uuid import uuid4

    doc_id = uuid4()
    s3_key = s3.key_for_document(doc_id=str(doc_id), filename=filename)

    await s3.put_object(key=s3_key, body=body, content_type="application/pdf")

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO documents (id, name, s3_key, size_bytes)
            VALUES ($4, $1, $2, $3)
            RETURNING id, name, s3_key, size_bytes
            """,
            filename,
            s3_key,
            size_bytes,
            doc_id,
        )

    if row is None:
        raise HTTPException(status_code=500, detail="failed to insert document row")

    return {"id": str(row["id"]), "name": row["name"]}


@router.get("")
async def list_documents(request: Request) -> list[dict]:
    db = request.app.state.db
    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, uploaded_at FROM documents ORDER BY uploaded_at DESC"
        )
    return [{"id": str(r["id"]), "name": r["name"]} for r in rows]


@router.get("/{doc_id}")
async def get_document(request: Request, doc_id: UUID) -> dict:
    db = request.app.state.db
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, s3_key, size_bytes FROM documents WHERE id = $1",
            doc_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {"id": str(row["id"]), "name": row["name"]}


@router.get("/{doc_id}/file")
async def get_document_file(request: Request, doc_id: UUID) -> Response:
    db = request.app.state.db
    s3 = request.app.state.s3
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT s3_key FROM documents WHERE id = $1",
            doc_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    body = await s3.get_object(key=row["s3_key"])
    return Response(content=body, media_type="application/pdf")


@router.delete("/{doc_id}")
async def delete_document(request: Request, doc_id: UUID) -> dict:
    db = request.app.state.db
    s3 = request.app.state.s3
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT s3_key FROM documents WHERE id = $1", doc_id)
        if row is None:
            raise HTTPException(status_code=404, detail="document not found")
        await s3.delete_object(key=row["s3_key"])
        await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)
    return {"deleted": str(doc_id)}
