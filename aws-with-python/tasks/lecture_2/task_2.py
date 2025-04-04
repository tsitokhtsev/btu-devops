import argparse
import json
from os import getenv
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import logging

load_dotenv()


def init_client():
    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=getenv("aws_access_key_id"),
            aws_secret_access_key=getenv("aws_secret_access_key"),
            aws_session_token=getenv("aws_session_token"),
            region_name=getenv("aws_region_name"),
        )

        client.list_buckets()

        return client
    except ClientError as e:
        logging.error(e)
    except Exception as e:
        logging.error("Unexpected error: {e}")


def bucket_policy_exists(client, bucket_name):
    try:
        client.get_bucket_policy(Bucket=bucket_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            return False
        else:
            logging.error(f"Error getting bucket policy: {e}")
            return False


def create_bucket_policy(client, bucket_name):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/dev/*",
                    f"arn:aws:s3:::{bucket_name}/test/*",
                ],
            }
        ],
    }

    policy_json = json.dumps(policy)

    try:
        client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)
        return True
    except ClientError as e:
        logging.error(f"Error creating bucket policy: {e}")
        return False


def check_block_public_policy(client, bucket_name):
    try:
        response = client.get_public_access_block(Bucket=bucket_name)
        return response["PublicAccessBlockConfiguration"]["BlockPublicPolicy"]
    except ClientError as e:
        logging.error(f"Error getting bucket policy status: {e}")
        return False


def disable_block_public_policy(client, bucket_name):
    try:
        client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        return True
    except ClientError as e:
        logging.error(f"Error disabling block public policy: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check if a bucket policy exists and create it if it does not"
    )
    parser.add_argument("bucket", type=str, help="Bucket name")
    args = parser.parse_args()

    bucket = args.bucket
    client = init_client()

    if not client:
        logging.error("Failed to initialize S3 client")
        return

    if bucket_policy_exists(client, bucket):
        print(f"Bucket policy for {bucket} already exists")
        return

    print(f"Bucket policy for {bucket} does not exist")

    if check_block_public_policy(client, bucket):
        print(f"Bucket {bucket} has BlockPublicPolicy enabled")

        if not disable_block_public_policy(client, bucket):
            print(f"Failed to disable BlockPublicPolicy for {bucket}")
            return

        print(f"BlockPublicPolicy for {bucket} disabled")

    if create_bucket_policy(client, bucket):
        print(f"Bucket policy for {bucket} created successfully")
    else:
        print(f"Failed to create bucket policy for {bucket}")


if __name__ == "__main__":
    main()
