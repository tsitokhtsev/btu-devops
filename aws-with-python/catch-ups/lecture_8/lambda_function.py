import io
import json
from pprint import pprint
from urllib.request import urlopen, Request
import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
from decimal import Decimal

API_TOKEN = ""

headers = {"Authorization": f"Bearer {API_TOKEN}"}
API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
DYNAMODB_TABLE = "your-dynamo-db"
s3_client = boto3.client("s3")


def query_image(f):
    http_request = Request(API_URL, data=f.read(), headers=headers)
    with urlopen(http_request) as response:
        result = response.read().decode()
        print(result)
    return result


def save_to_dynamodb(data):
    dynamodb = boto3.client("dynamodb")
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat()
    serializer = TypeSerializer()
    dynamo_serialized_data = []
    for item in json.loads(data, parse_float=Decimal):
        dynamo_serialized_item = {"M": {}}
        for key, value in item.items():
            if isinstance(value, (float, Decimal)):
                dynamo_serialized_item["M"][key] = {"N": str(value)}
            elif isinstance(value, dict):
                dynamo_serialized_item["M"][key] = {
                    "M": {k: serializer.serialize(v) for k, v in value.items()}
                }
            else:
                dynamo_serialized_item["M"][key] = {"S": str(value)}
        dynamo_serialized_data.append(dynamo_serialized_item)

    data_ready_to_be_saved = {
        "id": {"S": str(uuid.uuid1())},
        "createdAt": {"S": timestamp},
        "updatedAt": {"S": timestamp},
        "huggingJson": {"L": dynamo_serialized_data},
        "huggingFaceStringData": {"S": data},
    }
    print(json.dumps(data_ready_to_be_saved))

    try:
        dynamodb.put_item(TableName=DYNAMODB_TABLE, Item=data_ready_to_be_saved)
        pass
    except ClientError as e:
        print(e.response["Error"]["Message"])
        raise e
    return


def lambda_handler(event, _):
    pprint(event)
    for record in event.get("Records"):
        bucket = record.get("s3").get("bucket").get("name")
        key = record.get("s3").get("object").get("key")

        print("Bucket", bucket)
        print("Key", key)

        # Download file from bucket
        file = io.BytesIO()
        s3_client.download_fileobj(Bucket=bucket, Key=key, Fileobj=file)
        file.seek(0)

        # Send file to Huggingface API
        result = query_image(file)
        print("result", result)

        # save data to DynamoDB
        save_to_dynamodb(result)

    return {"statusCode": 200, "body": "Done!"}
