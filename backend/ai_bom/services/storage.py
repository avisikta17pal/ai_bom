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


def _sse_params() -> dict[str, Any]:
    settings = get_settings()
    if settings.s3.kms_key_id:
        return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": settings.s3.kms_key_id}
    return {"ServerSideEncryption": "AES256"}


def presign_put(key: str, expires_seconds: int = 900) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    params = {
        'Bucket': settings.s3.bucket,
        'Key': key,
    }
    params.update(_sse_params())
    url = s3.generate_presigned_url('put_object', Params=params, ExpiresIn=expires_seconds)
    return {'url': url, 'method': 'PUT', 'headers': {}}


def presign_get(key: str, expires_seconds: int = 300) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    params = {
        'Bucket': settings.s3.bucket,
        'Key': key,
    }
    url = s3.generate_presigned_url('get_object', Params=params, ExpiresIn=expires_seconds)
    return {'url': url, 'method': 'GET', 'headers': {}}


def create_multipart_upload(key: str) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    params = {
        'Bucket': settings.s3.bucket,
        'Key': key,
    }
    params.update(_sse_params())
    resp = s3.create_multipart_upload(**params)
    return {'uploadId': resp['UploadId']}


def presign_upload_part(key: str, upload_id: str, part_number: int, expires_seconds: int = 900) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    params = {
        'Bucket': settings.s3.bucket,
        'Key': key,
        'UploadId': upload_id,
        'PartNumber': part_number,
    }
    url = s3.generate_presigned_url('upload_part', Params=params, ExpiresIn=expires_seconds)
    return {'url': url, 'method': 'PUT', 'headers': {}}


def complete_multipart_upload(key: str, upload_id: str, parts: list[dict[str, Any]]) -> dict[str, Any]:  # pragma: no cover - external
    s3 = get_s3()
    settings = get_settings()
    resp = s3.complete_multipart_upload(
        Bucket=settings.s3.bucket,
        Key=key,
        MultipartUpload={'Parts': parts},
        UploadId=upload_id,
    )
    return {'etag': resp.get('ETag')}

