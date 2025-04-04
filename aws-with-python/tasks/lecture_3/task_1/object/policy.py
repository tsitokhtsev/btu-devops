def set_object_access_policy(aws_s3_client, bucket_name, file_name):
    response = aws_s3_client.put_object_acl(
        ACL="public-read", Bucket=bucket_name, Key=file_name
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def set_lifecycle_policy(aws_s3_client, bucket_name, days=120):
    lifecycle_configuration = {
        "Rules": [
            {
                "ID": f"Delete-after-{days}-days",
                "Status": "Enabled",
                "Expiration": {"Days": days},
                "Filter": {"Prefix": ""},
            }
        ]
    }

    try:
        response = aws_s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name, LifecycleConfiguration=lifecycle_configuration
        )
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Error setting lifecycle policy: {e}")
        return False
