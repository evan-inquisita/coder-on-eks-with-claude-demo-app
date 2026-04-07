"""Async S3 client wrapper using aioboto3.

The api container's bind-mounted ~/.aws picks up the IRSA -> access-role chain
that fetch-workspace-secrets.sh sets up at workspace startup. boto3 reads it
transparently -- we don't pass credentials explicitly anywhere.
"""

from __future__ import annotations

import re

import aioboto3


class S3Client:
    def __init__(self, bucket: str, region: str) -> None:
        self.bucket = bucket
        self.region = region
        self._session = aioboto3.Session()

    @staticmethod
    def key_for_document(doc_id: str, filename: str) -> str:
        """Build a deterministic, S3-safe key for a document upload."""
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
        return f"documents/{doc_id}/{safe}"

    async def put_object(self, key: str, body: bytes, content_type: str) -> None:
        async with self._session.client("s3", region_name=self.region) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )

    async def get_object(self, key: str) -> bytes:
        async with self._session.client("s3", region_name=self.region) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete_object(self, key: str) -> None:
        async with self._session.client("s3", region_name=self.region) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
