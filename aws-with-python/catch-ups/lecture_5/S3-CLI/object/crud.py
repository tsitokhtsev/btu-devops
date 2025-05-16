from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime
from os import getenv, stat
import pylibmagic
import magic
from pathlib import Path


def get_objects(aws_s3_client, bucket_name) -> str:
    for key in aws_s3_client.list_objects(Bucket=bucket_name)["Contents"]:
        print(f" {key['Key']}, size: {key['Size']}")


def generate_file_name(file_extension) -> str:
    return f'up_{md5(str(localtime()).encode("utf-8")).hexdigest()}.{file_extension}'


"""
usage:
object new-bucket-btu-7 -ol "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4" -du
object new-bucket-btu-7 -ol "https://www.adobe.com/express/feature/image/media_16ad2258cac6171d66942b13b8cd4839f0b6be6f3.png?width=750&format=png&optimize=medium" -du
object new-bucket-btu-7 -ol "https://img.lovepik.com/element/45012/9839.png_300.png" -du
"""


def download_file_and_upload_to_s3(
    aws_s3_client, bucket_name, url, s3_region=None, keep_local=True
) -> str:
    (s3_region := getenv("aws_s3_region_name", "us-west-2"))

    allowed_types = {"jpeg": "image/jpeg", "png": "image/png", "mp4": "video/mp4"}

    with urlopen(url) as response:
        content = response.read()
        mime_type = magic.from_buffer(content, mime=True)
        content_type = None
        file_name = None

        for type, ctype in allowed_types.items():
            if mime_type == ctype:
                content_type = ctype
                file_name = generate_file_name(type)

        if not content_type:
            raise ValueError("Invalid type")

        aws_s3_client.upload_fileobj(
            Fileobj=io.BytesIO(content),
            Bucket=bucket_name,
            ExtraArgs={"ContentType": content_type},
            Key=file_name,
        )

    if keep_local:
        with open(Path(f"static/{file_name}"), mode="wb") as file:
            file.write(content)

    # Public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        s3_region, bucket_name, file_name
    )


def multipart_upload(aws_s3_client, bucket_name, file_path, file_name, content_type):

    # https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html
    PART_BYTES = 5 * 1024 * 1024
    mpu = aws_s3_client.create_multipart_upload(
        Bucket=bucket_name, Key=file_name, ContentType=content_type
    )
    mpu_id = mpu["UploadId"]

    parts = []
    uploaded_bytes = 0
    total_bytes = stat(file_path).st_size
    with open(file_path, "rb") as f:
        i = 1
        while True:
            data = f.read(PART_BYTES)
            if not len(data):
                break
            part = aws_s3_client.upload_part(
                Body=data,
                Bucket=bucket_name,
                Key=file_name,
                UploadId=mpu_id,
                PartNumber=i,
            )
            parts.append({"PartNumber": i, "ETag": part["ETag"]})
            uploaded_bytes += len(data)
            print("{0} of {1} uploaded".format(uploaded_bytes, total_bytes))
            i += 1

    result = aws_s3_client.complete_multipart_upload(
        Bucket=bucket_name,
        Key=file_name,
        UploadId=mpu_id,
        MultipartUpload={"Parts": parts},
    )
    print(result)


"""
usage:
object new-bucket-btu-7 -loc_o hello.txt -u_t upload_fileobj
object new-bucket-btu-7 -loc_o hello.txt -u_t upload_fileobj
"""


def upload_local_file(
    aws_s3_client, bucket_name, filename, keep_file_name, upload_type="upload_file"
):

    allowed_types = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "mp4": "video/mp4",
        "txt": "text/plain",
    }

    file_path = Path(f"static/{filename}")
    mime_type = magic.from_file(file_path, mime=True)
    content_type = None
    file_name = None

    for type, ctype in allowed_types.items():
        if mime_type == ctype:
            content_type = ctype
            file_name = filename if keep_file_name else generate_file_name(type)

    if not content_type:
        raise ValueError("Invalid type")

    if upload_type == "upload_file":
        aws_s3_client.upload_file(
            file_path, bucket_name, file_name, ExtraArgs={"ContentType": content_type}
        )
    elif upload_type == "upload_fileobj":
        with open(file_path, "rb") as file:
            aws_s3_client.upload_fileobj(
                file, bucket_name, file_name, ExtraArgs={"ContentType": content_type}
            )
    elif upload_type == "put_object":
        with open(file_path, "rb") as file:
            aws_s3_client.put_object(
                Body=file.read(),
                Bucket=bucket_name,
                Key=file_name,
                ExtraArgs={"ContentType": content_type},
            )

    elif upload_type == "multipart_upload":
        multipart_upload(aws_s3_client, bucket_name, file_path, file_name, content_type)

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        getenv("aws_s3_region_name", "us-west-2"), bucket_name, file_name
    )


def delete_object(aws_s3_client, bucket_name, filename):
    # Check if object exists in the bucket
    response = aws_s3_client.list_objects_v2(Bucket=bucket_name, Prefix=filename)

    if "Contents" in response:
        # Delete the object if it exists
        aws_s3_client.delete_object(Bucket=bucket_name, Key=filename)

        print(
            f"The object with key '{filename}' has been deleted from bucket '{bucket_name}'."
        )
    else:
        print(
            f"The object with key '{filename}' does not exist in bucket '{bucket_name}'."
        )
