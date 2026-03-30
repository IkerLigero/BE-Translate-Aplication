import os
import boto3
from botocore.client import Config

# Forzamos la lectura del ENV
endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
# Nos aseguramos de que tenga el protocolo http
if not endpoint.startswith("http"):
    endpoint = f"http://{endpoint}"

s3_client = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def upload_pdf_to_minio(file_bytes, object_name):
    """Uploads PDF bytes to the configured MinIO bucket."""
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    s3_client.put_object(
        Bucket=bucket,
        Key=object_name,
        Body=file_bytes,
        ContentType="application/pdf"
    )

def get_pdf_from_minio(object_name):
    """Retrieves a file stream from MinIO."""
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    response = s3_client.get_object(Bucket=bucket, Key=object_name)
    return response['Body'] # This returns the stream for StreamingResponse