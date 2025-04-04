from botocore.exceptions import ClientError


def bucket_versioning_enabled(aws_s3_client, bucket_name) -> bool:
    try:
        response = aws_s3_client.get_bucket_versioning(Bucket=bucket_name)
        if "Status" in response and response["Status"] == "Enabled":
            return True
        else:
            return False
    except ClientError as e:
        print(f"Error checking versioning status: {e}")
        return False


def get_file_versions(aws_s3_client, bucket_name, filename):
    try:
        response = aws_s3_client.list_object_versions(
            Bucket=bucket_name, Prefix=filename
        )
        versions = response.get("Versions", [])

        print(f"Number of versions for {filename}: {len(versions)}")
        for version in versions:
            print(
                f"VersionId: {version['VersionId']}, LastModified: {version['LastModified']}"
            )
    except ClientError as e:
        print(f"Error listing object versions: {e}")


def upload_previous_file_version(aws_s3_client, bucket_name, filename):
    try:
        response = aws_s3_client.list_object_versions(
            Bucket=bucket_name, Prefix=filename
        )
        versions = response.get("Versions", [])

        if versions[1]:
            previous_version = versions[1]

            aws_s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={
                    "Bucket": bucket_name,
                    "Key": filename,
                    "VersionId": previous_version["VersionId"],
                },
                Key=filename,
            )

            return True
        else:
            print(f"No previous versions found for {filename}")
            return False
    except ClientError as e:
        print(f"Error uploading previous version: {e}")
        return False
