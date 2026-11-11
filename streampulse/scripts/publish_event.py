import json
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from botocore.config import Config


STREAM_NAME = "streampulse-playback"

kinesis = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    config=Config(
        connect_timeout=3,
        read_timeout=10,
        retries={"mode": "standard", "total_max_attempts": 3},
    ),
)


def main():
    event = {
        # str(uuid4()) generates a new event ID each time the script is ran
        "event_id": str(uuid4()), # identifies this particular event
        "event_type": "playback.progress", # describes what happened
        "user_id": "user-42", # identifies the viewer
        "session_id": "session-123", # identifies the viewing session
        "video_id": "movie-101", # identifies the video
        "position_seconds": 180, # records the playback position
        "occurred_at": datetime.now(timezone.utc).isoformat(), # records when the even happened in UTC
        "schema_version": 1, # identifies the event format version
    }

    event_bytes = json.dumps(event).encode("utf-8") # converts the python dictionary into JSON text, then into bytes for Kinesis

    # Calls Flocis Kinesis API to publish the bytes
    # The API accepts a stream name, data, and partition key, and returns a shard ID and sequence number
    response = kinesis.put_record(  
        StreamName=STREAM_NAME,
        Data=event_bytes,
        PartitionKey=event["user_id"], # Uses the user ID to determine which shard receives the record
    )

    print("Published event:")
    print(json.dumps(event, indent=2))

    print("\nKinesis acknowledgement:")
    print(f"Shard ID: {response['ShardId']}")
    print(f"Sequence number: {response['SequenceNumber']}")

    print("\nCopy and run this command to read the record:")
    print(
        r".\.venv\Scripts\python.exe scripts\read_event.py "
        f"--shard-id {response['ShardId']} "
        f"--sequence-number {response['SequenceNumber']}"
    )


if __name__ == "__main__":
    main()