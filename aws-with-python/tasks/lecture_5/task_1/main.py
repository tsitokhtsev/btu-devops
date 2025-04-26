import argparse
import boto3
import os
from os import getenv
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


def init_client(region: Optional[str] = None):
    """Initialize an S3 client with credentials from environment variables."""
    client = boto3.client(
        "s3",
        aws_access_key_id=getenv("aws_access_key_id"),
        aws_secret_access_key=getenv("aws_secret_access_key"),
        aws_session_token=getenv("aws_session_token"),
        region_name=region or getenv("aws_region_name"),
    )

    return client


def create_bucket(s3_client, bucket_name: str, region: Optional[str] = None):
    """Create an S3 bucket with the specified name."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} already exists")
    except:
        try:
            location = {"LocationConstraint": region} if region else {}
            if region is None or region == "us-east-1":
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=location,
                )
            print(f"Bucket {bucket_name} created")
        except Exception as e:
            print(f"Error creating bucket: {e}")
            raise


def configure_website(s3_client, bucket_name: str):
    """Configure the bucket for static website hosting."""
    website_configuration = {
        # "ErrorDocument": {"Key": "error.html"},
        "IndexDocument": {"Suffix": "index.html"},
    }

    s3_client.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration=website_configuration,
    )
    print(f"Bucket {bucket_name} configured for website hosting")


def set_bucket_policy(s3_client, bucket_name: str):
    """Set bucket policy to allow public read access."""
    try:
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        print(f"Disabled Block Public Access settings for bucket {bucket_name}")
    except Exception as e:
        print(f"Warning: Could not disable Block Public Access settings: {e}")
        print(
            "Your bucket may not be publicly accessible. Check your S3 console settings."
        )

    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
            }
        ],
    }

    import json

    bucket_policy_string = json.dumps(bucket_policy)

    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=bucket_policy_string,
        )
        print(f"Public read policy set for bucket {bucket_name}")
    except Exception as e:
        print(f"Warning: Could not set bucket policy: {e}")
        print("You may need to manually configure permissions in the AWS S3 console.")


def upload_local_directory(s3_client, bucket_name: str, directory_path: str):
    """Upload all files from a local directory to S3 bucket."""
    uploaded_files = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, directory_path)

            content_type = "text/html"
            if file.endswith(".css"):
                content_type = "text/css"
            elif file.endswith(".js"):
                content_type = "application/javascript"
            elif file.endswith(".jpg") or file.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file.endswith(".png"):
                content_type = "image/png"

            s3_client.upload_file(
                Filename=local_path,
                Bucket=bucket_name,
                Key=relative_path,
                ExtraArgs={"ContentType": content_type},
            )

            uploaded_files.append(relative_path)
            print(f"Uploaded {relative_path} to {bucket_name}")

    return uploaded_files


def get_website_url(bucket_name: str, region: Optional[str] = None):
    """Return the URL of the static website."""
    if region is None or region == "us-east-1":
        return f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
    else:
        return f"http://{bucket_name}.s3-website-{region}.amazonaws.com"


def main():
    parser = argparse.ArgumentParser(description="Host a website on Amazon S3")
    parser.add_argument("command", choices=["host"], help="Command to execute")
    parser.add_argument("bucket_name", help="Name of the S3 bucket to create")
    parser.add_argument(
        "--source", required=True, help="Local directory with website files"
    )
    parser.add_argument(
        "--region", default=None, help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    if args.command == "host":
        if not os.path.isdir(args.source):
            print(
                f"Error: Source directory '{args.source}' not found or is not a directory"
            )
            return 1

        s3_client = init_client(args.region)

        create_bucket(s3_client, args.bucket_name, args.region)
        configure_website(s3_client, args.bucket_name)
        set_bucket_policy(s3_client, args.bucket_name)
        upload_local_directory(s3_client, args.bucket_name, args.source)

        website_url = get_website_url(args.bucket_name, args.region)
        print(f"\nYour static website is now available at:\n{website_url}")

    return 0


if __name__ == "__main__":
    exit(main())
