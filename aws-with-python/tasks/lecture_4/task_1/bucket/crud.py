from botocore.exceptions import ClientError


def list_buckets(aws_s3_client) -> list:
    # https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_buckets.html
    return aws_s3_client.list_buckets()


def create_bucket(aws_s3_client, bucket_name, region) -> bool:
    location = {"LocationConstraint": region}
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
    response = aws_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration=location,
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def delete_bucket(aws_s3_client, bucket_name) -> bool:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_bucket.html
    response = aws_s3_client.delete_bucket(Bucket=bucket_name)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 204:
        return True
    return False


def bucket_exists(aws_s3_client, bucket_name) -> bool:
    try:
        response = aws_s3_client.head_bucket(Bucket=bucket_name)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code == 200:
            return True
    except ClientError:
        # print(e)
        return False
