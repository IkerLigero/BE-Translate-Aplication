import os
import boto3
from botocore.client import Config

# Internal endpoint: Used by the Backend/Worker to talk to MinIO (e.g., inside Docker)
SERVER_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")

# External endpoint: Used for generating URLs that the Browser can reach.
# This ensures the link starts with 'localhost' or a public IP instead of a Docker alias.
BROWSER_ENDPOINT = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")

# Client for internal operations (upload, stream retrieval)
s3_client = boto3.client(
    's3',
    endpoint_url=SERVER_ENDPOINT,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# Dedicated client for presigned URLs using the browser-accessible endpoint
s3_presigned_client = boto3.client(
    's3',
    endpoint_url=BROWSER_ENDPOINT,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# --- Storage Functions ---
def upload_pdf_to_minio(file_bytes: bytes, object_name: str):
    """
    Uploads PDF bytes to the configured MinIO bucket.
    """
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    s3_client.put_object(
        Bucket=bucket,
        Key=object_name,
        Body=file_bytes,
        ContentType="application/pdf"
    )

# This function generates a presigned URL that the frontend can use to download the PDF directly from MinIO, without going through the backend.
def get_pdf_from_minio(object_name: str):
    """
    Retrieves a file stream from MinIO using the internal client.
    """
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    response = s3_client.get_object(Bucket=bucket, Key=object_name)
    return response['Body']