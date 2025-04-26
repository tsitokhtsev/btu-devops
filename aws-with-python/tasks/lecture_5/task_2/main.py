import argparse
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import json
from os import getenv
from time import localtime
from typing import Optional
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4


load_dotenv()

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}


def init_client(region: Optional[str] = None):
    """Initialize an S3 client with credentials from environment variables."""
    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=getenv("aws_access_key_id"),
            aws_secret_access_key=getenv("aws_secret_access_key"),
            aws_session_token=getenv("aws_session_token"),
            region_name=region or getenv("aws_region_name"),
        )
        return client
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return None


def bucket_exists(s3_client, bucket_name: str) -> bool:
    """Check if the specified S3 bucket exists and is accessible."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        return False


def save_quote_to_s3(s3_client, bucket_name: str, quote_data: dict):
    """Save a quote to an S3 bucket as a JSON file."""
    if not s3_client:
        print("Error: S3 client not initialized")
        return False

    if not bucket_exists(s3_client, bucket_name):
        print(f"Error: Bucket {bucket_name} does not exist or is not accessible")
        return False

    try:
        file_name = f"quote_{uuid4()}.json"
        json_data = json.dumps(quote_data, indent=2)

        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_data,
            ContentType="application/json",
        )

        print(f"Quote saved to s3://{bucket_name}/{file_name}")
        return True
    except ClientError as e:
        print(f"Error saving quote to S3: {e}")
        return False


def get_quote(author: Optional[str] = None):
    """Generic function to fetch data from the quotes API."""
    base_url = "https://api.quotable.kurokeita.dev/api/quotes/random"
    url = f"{base_url}?author={quote(author)}" if author else base_url

    try:
        with urlopen(Request(url, data=None, headers=headers)) as response:
            result = json.loads(response.read().decode())
            return result if result else None
    except Exception as e:
        print(f"Error fetching quote: {e}")
        return None


def print_quote(quote: dict):
    """Print the quote in a formatted way."""
    print(quote["quote"]["content"])
    print("---")
    print(quote["quote"]["author"]["name"])


def main():
    parser = argparse.ArgumentParser(
        description="CLI program for fetching and managing inspirational quotes."
    )

    parser.add_argument(
        "bucket_name",
        nargs="?",
        type=str,
        help="Name of the S3 bucket to save quotes (optional)",
    )

    parser.add_argument(
        "--inspire",
        nargs="?",
        const=True,
        help="Fetch a random inspirational quote. Optionally specify an author name.",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the quote to the specified S3 bucket",
    )

    args = parser.parse_args()

    if args.inspire is not None:
        if args.inspire is True:
            quote = get_quote()
        else:
            quote = get_quote(args.inspire)

        if quote:
            print_quote(quote)

            if args.save:
                if args.bucket_name:
                    s3_client = init_client()
                    save_quote_to_s3(s3_client, args.bucket_name, quote)
                else:
                    print("Error: Bucket name is required with --save flag")
        else:
            print("No quotes found.")
        return


if __name__ == "__main__":
    main()
