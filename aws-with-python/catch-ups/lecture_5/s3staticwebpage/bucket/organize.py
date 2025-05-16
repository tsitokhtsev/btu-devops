def object_per_extension(aws_s3_client, bucket_name):
    for each in aws_s3_client.list_objects_v2(Bucket=bucket_name).get("Contents", []):
        extension_folder = "unknown"
        if "." in each["Key"]:
            extension_folder = each["Key"].split(".")[-1]
            aws_s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={"Bucket": bucket_name, "Key": each["Key"]},
                Key=f"{extension_folder}/{each['Key']}",
            )
            aws_s3_client.delete_object(Bucket=bucket_name, Key=each["Key"])
        else:
            aws_s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={"Bucket": bucket_name, "Key": each["Key"]},
                Key=f"{extension_folder}/{each['Key']}",
            )
            aws_s3_client.delete_object(Bucket=bucket_name, Key=each["Key"])
