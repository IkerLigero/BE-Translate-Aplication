import os
import boto3
from botocore.client import Config

# Force reading the ENV
endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
# Ensure it has the http protocol
if not endpoint.startswith("http"):
    endpoint = f"http://{endpoint}"

# Initialize the MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# This function is used by the Worker to upload the generated PDF to MinIO.
def upload_pdf_to_minio(file_bytes, object_name):
    """Uploads PDF bytes to the configured MinIO bucket."""
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    s3_client.put_object(
        Bucket=bucket,
        Key=object_name,
        Body=file_bytes,
        ContentType="application/pdf"
    )

# This function can be used to retrieve the PDF stream for the download endpoint.
def get_pdf_from_minio(object_name):
    """Retrieves a file stream from MinIO."""
    bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
    response = s3_client.get_object(Bucket=bucket, Key=object_name)
    return response['Body'] # This returns the stream for StreamingResponse