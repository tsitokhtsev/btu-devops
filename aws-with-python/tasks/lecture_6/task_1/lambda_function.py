import io
import json
import os
import urllib.parse
from urllib.request import Request, urlopen

import boto3

API_TOKEN = os.environ.get("API_TOKEN")
MODELS = {
    "mobilenet": "google/mobilenet_v1_0.75_192",
    "resnet": "microsoft/resnet-50",
    "mit": "nvidia/mit-b0",
    "yolos": "hustvl/yolos-tiny",
}


s3_client = boto3.client("s3")


def query_image(image_data, model_url, image_content_type):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": image_content_type,
    }
    api_url = f"https://api-inference.huggingface.co/models/{model_url}"
    http_request = Request(api_url, data=image_data, headers=headers)

    with urlopen(http_request) as response:
        result = response.read().decode()
    return result


def lambda_handler(event, _):
    for record in event.get("Records"):
        bucket = record.get("s3").get("bucket").get("name")
        key = urllib.parse.unquote_plus(record.get("s3").get("object").get("key"))

        print(f"Processing image from Bucket: {bucket}, Key: {key}")

        if not key.lower().endswith((".jpg", ".jpeg", ".png")):
            print(f"Skipping non-image file: {key}")
            continue

        image_name = os.path.basename(key).split(".")[0]
        image_extension = os.path.splitext(key)[1].lower()
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(image_extension, "application/octet-stream")

        file = io.BytesIO()
        s3_client.download_fileobj(Bucket=bucket, Key=key, Fileobj=file)
        file.seek(0)
        image_data = file.read()

        for model_name, model_url in MODELS.items():
            try:
                print(f"Processing with model: {model_name}")

                file_copy = io.BytesIO(image_data)
                result = query_image(file_copy, model_url, content_type)
                result_key = f"json/{model_name}_{image_name}.json"

                result_file = io.BytesIO(result.encode("utf-8"))
                result_file.seek(0)
                s3_client.upload_fileobj(result_file, bucket, result_key)
                print(f"Uploaded result to {result_key}")
            except Exception as e:
                print(f"Error processing with model {model_name}: {str(e)}")

    return {"statusCode": 200, "body": json.dumps("Done!")}
