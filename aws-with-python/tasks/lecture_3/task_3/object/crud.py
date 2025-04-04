import os
from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime

PART_BYTES = 5 * 1024 * 1024


def get_objects(aws_s3_client, bucket_name) -> str:
    for key in aws_s3_client.list_objects(Bucket=bucket_name)["Contents"]:
        print(f" {key['Key']}, size: {key['Size']}")


def download_file_and_upload_to_s3(
    aws_s3_client, bucket_name, url, keep_local=False
) -> str:
    file_name = f'image_file_{md5(str(localtime()).encode("utf-8")).hexdigest()}.jpg'
    with urlopen(url) as response:
        content = response.read()
        aws_s3_client.upload_fileobj(
            Fileobj=io.BytesIO(content),
            Bucket=bucket_name,
            ExtraArgs={"ContentType": "image/jpg"},
            Key=file_name,
        )
    if keep_local:
        with open(file_name, mode="wb") as jpg_file:
            jpg_file.write(content)

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        "us-west-2", bucket_name, file_name
    )


def upload_file(aws_s3_client, filename, bucket_name):
    try:
        aws_s3_client.upload_file(filename, bucket_name, "hello.txt")
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False


def upload_file_obj(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.upload_fileobj(file, bucket_name, "hello_obj.txt")


def upload_file_put(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.put_object(
            Bucket=bucket_name, Key="hello_put.txt", Body=file.read()
        )


def multipart_upload(aws_s3_client, filename, bucket_name):
    mpu = aws_s3_client.create_multipart_upload(Bucket=bucket_name, Key=filename)
    mpu_id = mpu["UploadId"]

    parts = []
    uploaded_bytes = 0
    total_bytes = os.stat(filename).st_size

    with open(filename, "rb") as f:
        i = 1

        while True:
            data = f.read(PART_BYTES)

            if not len(data):
                break

            part = aws_s3_client.upload_part(
                Body=data,
                Bucket=bucket_name,
                Key=filename,
                UploadId=mpu_id,
                PartNumber=i,
            )
            parts.append({"PartNumber": i, "ETag": part["ETag"]})
            uploaded_bytes += len(data)
            print("{0} of {1} uploaded".format(uploaded_bytes, total_bytes))
            i += 1

    try:
        aws_s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=filename,
            UploadId=mpu_id,
            MultipartUpload={"Parts": parts},
        )
        return True
    except Exception as e:
        print(f"Error completing multipart upload: {e}")
        return False


def delete_file(aws_s3_client, bucket_name, filename):
    try:
        aws_s3_client.delete_object(Bucket=bucket_name, Key=filename)
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
