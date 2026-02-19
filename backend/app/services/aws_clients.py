import boto3

from app.core.config import Settings


def s3_client(settings: Settings):
    return boto3.client("s3", region_name=settings.aws_region)


def ses_client(settings: Settings):
    return boto3.client("ses", region_name=settings.aws_region)
