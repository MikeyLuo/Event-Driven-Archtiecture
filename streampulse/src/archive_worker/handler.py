import base64
import json
import os

import boto3
from botocore.config import Config


BUCKET_NAME = os.environ["EVENT_ARCHIVE_BUCKET"]

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["FLOCI_ENDPOINT_URL"],
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    config=Config(
        s3={"addressing_style": "path"},
        connect_timeout=3,
        read_timeout=5,
        retries={"mode": "standard", "total_max_attempts": 2},
    ),
)


def lambda_handler(event, context):
    records = event["Records"]

    for record in records:
        event_bytes = base64.b64decode(record["kinesis"]["data"])
        playback = json.loads(event_bytes)
        event_id = playback["event_id"]
        object_key = f"playback/{event_id}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=event_bytes,
            ContentType="application/json",
        )

        print(f"Archived event {event_id} to s3://{BUCKET_NAME}/{object_key}")

    return {"archived": len(records)}