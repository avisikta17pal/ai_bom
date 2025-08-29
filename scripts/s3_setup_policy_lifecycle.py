import json
from ai_bom.core.config import get_settings
import boto3


def main():  # pragma: no cover
    settings = get_settings()
    s3 = boto3.client(
        's3',
        endpoint_url=(f"https://{settings.s3.endpoint}" if settings.s3.secure else f"http://{settings.s3.endpoint}"),
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )
    try:
        s3.create_bucket(Bucket=settings.s3.bucket)
    except Exception:
        pass
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [f"arn:aws:s3:::{settings.s3.bucket}", f"arn:aws:s3:::{settings.s3.bucket}/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            }
        ],
    }
    s3.put_bucket_policy(Bucket=settings.s3.bucket, Policy=json.dumps(policy))
    lifecycle = {
        "Rules": [
            {"ID": "expire-multiparts", "Status": "Enabled", "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}},
            {"ID": "transition-logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"}, "Expiration": {"Days": 365}},
        ]
    }
    s3.put_bucket_lifecycle_configuration(Bucket=settings.s3.bucket, LifecycleConfiguration=lifecycle)
    print("S3 bucket policy and lifecycle configured.")


if __name__ == "__main__":
    main()

