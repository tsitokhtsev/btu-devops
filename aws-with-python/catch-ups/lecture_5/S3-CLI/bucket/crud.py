from botocore.exceptions import ClientError


def list_buckets(aws_s3_client) -> list:
    # https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_buckets.html
    return aws_s3_client.list_buckets()


def create_bucket(aws_s3_client, bucket_name, region) -> bool:
    location = {"LocationConstraint": region}
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
    response = aws_s3_client.create_bucket(
        Bucket=bucket_name, CreateBucketConfiguration=location
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


def purge_bucket(aws_s3_client, bucket_name):

    object_keys = []
    # Get a list of all objects in the bucket
    for obj in aws_s3_client.list_objects(Bucket=bucket_name)["Contents"]:
        # Extract the object keys
        object_keys.append({"Key": obj["Key"]})

    # Delete all objects in the bucket
    response = aws_s3_client.delete_objects(
        Bucket=bucket_name, Delete={"Objects": object_keys}
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def show_bucket_tree(aws_s3_client, bucket_name, prefix, is_last):
    if prefix:
        print(prefix + ("└── " if is_last else "├── ") + prefix.split("/")[-2])
    else:
        print(prefix)

    prefix += "" if is_last else "│  "

    response = aws_s3_client.list_objects_v2(
        Bucket=bucket_name, Delimiter="/", Prefix=prefix
    )

    # If there are no subdirectories or files, return
    if "CommonPrefixes" not in response and "Contents" not in response:
        return

    # If there are subdirectories, recursively call show_bucket_tree() for each subdirectory
    if "CommonPrefixes" in response:
        num_prefixes = len(response["CommonPrefixes"])
        for i, sub_prefix in enumerate(response["CommonPrefixes"]):
            is_last_subdir = i == num_prefixes - 1
            show_bucket_tree(
                aws_s3_client, bucket_name, sub_prefix["Prefix"], is_last_subdir
            )

    # If there are files, print each file's name with the appropriate formatting
    if "Contents" in response:
        num_files = len(response["Contents"])
        for i, file in enumerate(response["Contents"]):
            is_last_file = i == num_files - 1
            print(
                prefix
                + ("└── " if is_last_file else "├── ")
                + file["Key"].split("/")[-1]
            )
