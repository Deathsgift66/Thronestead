import json
import os
from datetime import datetime

import boto3

from backend.supabase_client import get_supabase_client


def main() -> None:
    sb = get_supabase_client()
    data = sb.table("users").select("*").execute()
    rows = data.data if hasattr(data, "data") else data.get("data")
    bucket = os.environ.get("BACKUP_BUCKET")
    if not bucket:
        raise RuntimeError("BACKUP_BUCKET not set")
    key = f"users_backup_{datetime.utcnow().date()}.json"
    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(rows).encode("utf-8"))
    print(f"Uploaded {len(rows)} records to s3://{bucket}/{key}")


if __name__ == "__main__":
    main()
