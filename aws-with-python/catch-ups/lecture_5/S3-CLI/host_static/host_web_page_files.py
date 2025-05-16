
from pathlib import Path
from os import getenv
from bucket.crud import bucket_exists
import pylibmagic
import magic


def static_web_page_file(aws_s3_client, bucket_name, filename):
    if not bucket_exists(aws_s3_client, bucket_name):
        raise ValueError("Bucket does not exists")

    root = Path(f'static_web_page/{filename}').expanduser().resolve()

    def __handle_directory(file_folder):
        if file_folder.is_file():
            __upload_static_web_files(aws_s3_client, bucket_name, file_folder, filename)
            return
        for each_path in file_folder.iterdir():
            if each_path.is_dir():
                __handle_directory(each_path)
            if each_path.is_file():
                __upload_static_web_files(aws_s3_client, bucket_name, each_path, str(each_path.relative_to(root)))

    __handle_directory(root)

    # public URL
    return "http://{0}.s3-website-{1}.amazonaws.com".format(
        bucket_name,
        getenv("aws_s3_region_name", "us-west-2")
    )


def __upload_static_web_files(aws_s3_client, bucket_name, file_path, filename):
    uploaded = {}

    mime_type = magic.from_file(file_path, mime=True)

    allowed_types = {
        ".html": "text/html",
        ".css": "text/plain"
    }

    content_type = mime_type if mime_type in allowed_types.values() else None

    if ".css" == file_path.suffix:
        content_type = "text/css"

    if content_type:
        aws_s3_client.upload_file(
            file_path,
            bucket_name,
            filename,
            ExtraArgs={'ContentType': content_type}
        )
        uploaded[file_path] = filename
        print(content_type, mime_type)
