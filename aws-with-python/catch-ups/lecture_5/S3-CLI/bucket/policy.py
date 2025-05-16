import json


def public_read_policy(bucket_name):
    policy = {
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

    return json.dumps(policy)


def multiple_policy(bucket_name):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "s3:ListBucketVersions",
                    "s3:PutObjectAcl",
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                    "s3:DeleteObject",
                ],
                "Resource": "*",
                "Effect": "Allow",
                "Principal": "*",
            }
        ],
    }

    return json.dumps(policy)


def assign_policy(aws_s3_client, policy_function, bucket_name):
    policy = None
    response = None
    if policy_function == "public_read_policy":
        policy = public_read_policy(bucket_name)
        response = "public read policy assigned!"
    elif policy_function == "multiple_policy":
        policy = multiple_policy(bucket_name)
        response = "multiple policy assigned!"

    if not policy:
        print("please provide policy")
        return

    aws_s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy)

    print(response)


def read_bucket_policy(aws_s3_client, bucket_name):
    policy = aws_s3_client.get_bucket_policy(Bucket=bucket_name)

    status_code = policy["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return policy["Policy"]
    return False
