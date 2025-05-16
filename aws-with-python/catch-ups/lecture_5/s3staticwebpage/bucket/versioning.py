#  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_bucket_versioning.html#put-bucket-versioning


def versioning(aws_s3_client, bucket_name, status: bool):
    versioning_status = "Enabled" if status else "Suspended"
    aws_s3_client.put_bucket_versioning(
        Bucket=bucket_name, VersioningConfiguration={"Status": versioning_status}
    )
