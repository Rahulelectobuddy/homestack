import io
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from minio import Minio
except ImportError:
    Minio = None


class DataLakeWriter:
    """S3 / MinIO data lake write helper enforcing consistent partitioning and file schemas."""

    def __init__(self, minio_endpoint: str, access_key: str = "minioadmin", secret_key: str = "minioadmin", secure: bool = False):
        """Initialize S3 client connection to MinIO data lake endpoint.
        
        Args:
            minio_endpoint: MinIO server hostname and port (e.g. 'minio:9000' or '192.168.1.10:9000').
            access_key: MinIO root access key credential.
            secret_key: MinIO root secret key credential.
            secure: Use HTTPS if True, HTTP if False.
        """
        endpoint = minio_endpoint.replace("http://", "").replace("https://", "")
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if Minio is None:
                raise ImportError("minio package is required for DataLakeWriter. Install via 'pip install minio'")
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
        return self._client

    def _ensure_bucket(self, bucket: str):
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except Exception as e:
            print(f"[DataLakeWriter] Warning: Could not verify/create bucket '{bucket}': {e}")

    def write_json(self, bucket: str, dataset: str, data: Any, partition_keys: Optional[Dict[str, str]] = None) -> str:
        """Write raw JSON payloads into specified MinIO bucket with Hive partition key prefixes.
        
        Args:
            bucket: Target S3 bucket (e.g. 'raw-data').
            dataset: Dataset identifier (e.g. 'bus_scraper', 'health_ingester', 'irrigation').
            data: List or dict of payload data.
            partition_keys: Optional partition key-value dict (e.g. {'year': '2026', 'month': '09', 'day': '26'}).
            
        Returns:
            The full S3 URI where the object was stored.
        """
        self._ensure_bucket(bucket)
        now = datetime.now(timezone.utc)
        if not partition_keys:
            partition_keys = {
                "year": now.strftime("%Y"),
                "month": now.strftime("%m"),
                "day": now.strftime("%d")
            }

        partition_path = "/".join(f"{k}={v}" for k, v in partition_keys.items())
        filename = f"{dataset}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        object_name = f"{dataset}/{partition_path}/{filename}"

        json_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes),
            content_type="application/json"
        )
        return f"s3://{bucket}/{object_name}"

    def write_csv(self, bucket: str, dataset: str, csv_content: str, partition_keys: Optional[Dict[str, str]] = None) -> str:
        """Write CSV string content into specified MinIO bucket with Hive partition key prefixes."""
        self._ensure_bucket(bucket)
        now = datetime.now(timezone.utc)
        if not partition_keys:
            partition_keys = {
                "year": now.strftime("%Y"),
                "month": now.strftime("%m"),
                "day": now.strftime("%d")
            }

        partition_path = "/".join(f"{k}={v}" for k, v in partition_keys.items())
        filename = f"{dataset}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        object_name = f"{dataset}/{partition_path}/{filename}"

        csv_bytes = csv_content.encode('utf-8')

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(csv_bytes),
            length=len(csv_bytes),
            content_type="text/csv"
        )
        return f"s3://{bucket}/{object_name}"

    def write_parquet(self, bucket: str, dataset: str, dataframe: Any, partition_cols: Optional[List[str]] = None) -> str:
        """Write pandas/polars DataFrames into Apache Parquet format inside curated S3 buckets."""
        self._ensure_bucket(bucket)
        now = datetime.now(timezone.utc)
        partition_path = f"year={now.strftime('%Y')}/month={now.strftime('%m')}"
        filename = f"data_{now.strftime('%Y%m%d_%H%M%S')}.parquet"
        object_name = f"{dataset}/{partition_path}/{filename}"

        buf = io.BytesIO()
        dataframe.to_parquet(buf, index=False)
        buf.seek(0)
        parquet_bytes = buf.getvalue()

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(parquet_bytes),
            length=len(parquet_bytes),
            content_type="application/octet-stream"
        )
        return f"s3://{bucket}/{object_name}"

