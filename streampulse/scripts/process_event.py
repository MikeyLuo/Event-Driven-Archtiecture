import argparse
import base64
import json
import time

import boto3
from botocore.config import Config

from src.playback_worker.handler import lambda_handler, table


kinesis = boto3.client(
    "kinesis",
    endpoint_url="http://127.0.0.1:4566",
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
    parser = argparse.ArgumentParser(
        description="Process one Kinesis record into DynamoDB."
    )

    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--sequence-number", required=True)

    args = parser.parse_args()

    response = kinesis.get_shard_iterator(
        StreamName="streampulse-playback",
        ShardId=args.shard_id,
        ShardIteratorType="AT_SEQUENCE_NUMBER",
        StartingSequenceNumber=args.sequence_number,
    )

    iterator = response["ShardIterator"]

    for attempt in range(1, 11):
        response = kinesis.get_records(
            ShardIterator=iterator,
            Limit=10,
        )

        for record in response["Records"]:
            if record["SequenceNumber"] != args.sequence_number:
                continue

            playback = json.loads(record["Data"].decode("utf-8"))

            lambda_event = {
                "Records": [
                    {
                        "kinesis": {
                            "data": base64.b64encode(
                                record["Data"]
                            ).decode("ascii"),
                            "partitionKey": record["PartitionKey"],
                            "sequenceNumber": record["SequenceNumber"],
                        }
                    }
                ]
            }

            result = lambda_handler(lambda_event, None)
            print(f"Worker result: {result}")

            response = table.get_item(
                Key={
                    "user_id": playback["user_id"],
                    "video_id": playback["video_id"],
                },
                ConsistentRead=True,
            )

            saved = response.get("Item")

            if (
                saved is None
                or saved["last_event_id"] != playback["event_id"]
                or saved["position_seconds"]
                != playback["position_seconds"]
            ):
                raise SystemExit(
                    "FAIL: Saved progress does not match the event."
                )

            print("\nPASS: DynamoDB contains the matching progress.")
            print(f"User: {saved['user_id']}")
            print(f"Video: {saved['video_id']}")
            print(f"Position: {saved['position_seconds']}")
            print(f"Last event ID: {saved['last_event_id']}")

            return

        iterator = response.get("NextShardIterator")

        if not iterator:
            break

        print(f"Waiting for record; poll {attempt}/10.")
        time.sleep(1)

    raise SystemExit("Requested Kinesis record was not found.")


if __name__ == "__main__":
    main()