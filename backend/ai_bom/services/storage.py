from __future__ import annotations

from datetime import timedelta, datetime
from typing import Any

import boto3

from ai_bom.core.config import get_settings


def get_s3():  # pragma: no cover - external
    settings = get_settings()
    return boto3.client(
        's3',
        endpoint_url=(f"https://{settings.s3.endpoint}" if settings.s3.secure else f"http://{settings.s3.endpoint}"),
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )


def presign_put(key: str, expires_seconds: int = 900) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    params = {
        'Bucket': settings.s3.bucket,
        'Key': key,
        'ServerSideEncryption': 'AES256',
    }
    url = s3.generate_presigned_url('put_object', Params=params, ExpiresIn=expires_seconds)
    return {'url': url, 'method': 'PUT', 'headers': {}}

