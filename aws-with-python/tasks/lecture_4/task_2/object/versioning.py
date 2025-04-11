from datetime import datetime, timedelta, timezone


def list_object_versions(aws_s3_client, bucket_name, file_name):
    versions = aws_s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix=file_name,
    )

    for version in versions["Versions"]:
        version_id = version["VersionId"]
        file_key = (version["Key"],)
        is_latest = version["IsLatest"]
        modified_at = version["LastModified"]

        # response = aws_s3_client.get_object(
        #     Bucket=bucket_name,
        #     Key=file_key[0],
        #     VersionId=version_id,
        # )
        # data = response['Body'].read()

        print(version_id, file_key, is_latest, modified_at)


def rollback_to_version(aws_s3_client, bucket_name, file_name, version):
    aws_s3_client.copy_object(
        Bucket=bucket_name,
        Key=file_name,
        CopySource={"Bucket": bucket_name, "Key": file_name, "VersionId": version},
    )


def delete_old_versions(aws_s3_client, bucket_name, file_name, months_old=6):
    print(f"Checking versions for {file_name}...")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=months_old * 30)
    paginator = aws_s3_client.get_paginator("list_object_versions")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=file_name)
    versions_to_delete = []

    for page in page_iterator:
        if "Versions" in page:
            for version in page["Versions"]:
                if version["Key"] == file_name:
                    last_modified_date = version["LastModified"]
                    if not version["IsLatest"] and last_modified_date < cutoff_date:
                        versions_to_delete.append(
                            {"Key": file_name, "VersionId": version["VersionId"]}
                        )
                        print(
                            f"  Marking for deletion: VersionId={version['VersionId']}, LastModified={last_modified_date.strftime('%Y-%m-%d')}, IsLatest={version['IsLatest']}"
                        )

    if versions_to_delete:
        aws_s3_client.delete_objects(
            Bucket=bucket_name,
            Delete={
                "Objects": versions_to_delete,
                "Quiet": True,
            },
        )
        print(
            f"Finished cleanup for {file_name}. Deleted {len(versions_to_delete)} old versions\n"
        )
    else:
        print(f"No versions older than {months_old} months found for {file_name}\n")
