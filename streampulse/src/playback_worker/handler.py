import base64
import json
import os

import boto3
from botocore.config import Config


TABLE_NAME = os.getenv(
    "WATCH_PROGRESS_TABLE",
    "streampulse-watch-progress",
)

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=os.getenv(
        "FLOCI_ENDPOINT_URL",
        "http://127.0.0.1:4566",
    ),
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    config=Config(
        connect_timeout=3,
        read_timeout=10,
        retries={"mode": "standard", "total_max_attempts": 3},
    ),
)

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    processed = 0

    for record in event["Records"]:
        event_bytes = base64.b64decode(record["kinesis"]["data"])
        playback = json.loads(event_bytes.decode("utf-8"))

        if playback["schema_version"] != 1:
            raise ValueError("Unsupported event schema version")

        if playback["event_type"] != "playback.progress":
            raise ValueError("Unsupported event type")

        position = playback["position_seconds"]

        if type(position) is not int or position < 0:
            raise ValueError(
                "position_seconds must be a non-negative integer"
            )

        item = {
            "user_id": playback["user_id"],
            "video_id": playback["video_id"],
            "session_id": playback["session_id"],
            "position_seconds": position,
            "last_event_id": playback["event_id"],
            "last_event_at": playback["occurred_at"],
        }

        table.put_item(Item=item) # creates an item or replaces the exisiting item with the same primary key -- primary key is the combo of user_id and video_id

        print(
            f"Saved progress: user={item['user_id']} "
            f"video={item['video_id']} "
            f"position={position} "
            f"event_id={item['last_event_id']}"
        )

        processed += 1

    return {"processed": processed}