import argparse
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


def bucket_exists(client, bucket_name):
    try:
        client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            logging.error(f"Error getting bucket: {e}")
            return False


def delete_bucket(client, bucket_name):
    try:
        client.delete_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        logging.error(f"Error deleting bucket: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check if a bucket exists and delete it if it does"
    )
    parser.add_argument("bucket", type=str, help="Bucket name")
    args = parser.parse_args()

    bucket = args.bucket
    client = init_client()

    if not client:
        logging.error("Failed to initialize S3 client")
        return

    if not bucket_exists(client, bucket):
        print(f"Bucket {bucket} does not exist")
        return

    print(f"Bucket policy for {bucket} exists")

    if delete_bucket(client, bucket):
        print(f"Bucket {bucket} deleted successfully")
    else:
        print(f"Failed to delete bucket {bucket}")


if __name__ == "__main__":
    main()
