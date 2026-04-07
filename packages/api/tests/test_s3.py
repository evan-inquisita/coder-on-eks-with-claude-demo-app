# packages/api/tests/test_s3.py
from doc_chat_api.s3 import S3Client


def test_s3_client_constructor_stores_bucket_and_region() -> None:
    c = S3Client(bucket="my-bucket", region="us-east-1")
    assert c.bucket == "my-bucket"
    assert c.region == "us-east-1"


def test_s3_client_key_for_document_uses_uuid_prefix() -> None:
    c = S3Client(bucket="b", region="us-east-1")
    key = c.key_for_document(doc_id="abc-123", filename="research paper.pdf")
    # spaces should be replaced; the doc id should be in the key
    assert "abc-123" in key
    assert key.endswith(".pdf")
    assert " " not in key
