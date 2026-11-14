import base64
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


STREAM_NAME = os.environ["PLAYBACK_STREAM_NAME"]

kinesis = boto3.client(
    "kinesis",
    endpoint_url=os.environ["FLOCI_ENDPOINT_URL"],
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    config=Config(
        connect_timeout=3,
        read_timeout=5,
        retries={"mode": "standard", "total_max_attempts": 2},
    ),
)


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    body = event.get("body")
    if not isinstance(body, str):
        return json_response(400, {"error": "A JSON body is required."})

    try:
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body, validate=True)
        payload = json.loads(body)
    except ValueError:
        return json_response(400, {"error": "The body must be valid JSON."})

    if not isinstance(payload, dict):
        return json_response(400, {"error": "The body must be a JSON object."})

    playback = {}
    for field in ("user_id", "session_id", "video_id"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            return json_response(
                400, {"error": f"{field} must be a nonempty string up to 256 characters."}
            )
        playback[field] = value.strip()

    position = payload.get("position_seconds")
    if type(position) is not int or position < 0:
        return json_response(
            400, {"error": "position_seconds must be a non-negative integer."}
        )

    playback.update(
        event_id=str(uuid4()),
        event_type="playback.progress",
        position_seconds=position,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        schema_version=1,
    )

    try:
        kinesis.put_record(
            StreamName=STREAM_NAME,
            PartitionKey=playback["user_id"],
            Data=json.dumps(playback).encode("utf-8"),
        )
    except (BotoCoreError, ClientError) as exc:
        print(f"Failed to publish event {playback['event_id']}: {exc}")
        return json_response(503, {"error": "Could not publish the playback event."})

    return json_response(202, {"event_id": playback["event_id"]})