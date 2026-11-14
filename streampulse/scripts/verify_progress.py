import argparse
import time

import boto3
from botocore.config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", required=True)
    args = parser.parse_args()

    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url="http://127.0.0.1:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(
            connect_timeout=3,
            read_timeout=5,
            retries={"total_max_attempts": 1},
        ),
    )
    table = dynamodb.Table("streampulse-watch-progress")

    for attempt in range(1, 31):
        response = table.get_item(
            Key={"user_id": "user-42", "video_id": "movie-101"},
            ConsistentRead=True,
        )
        item = response.get("Item")

        if item and item.get("last_event_id") == args.event_id:
            print("PASS: Lambda automatically saved this event.")
            print(f"Position: {item['position_seconds']}")
            print(f"Event ID: {item['last_event_id']}")
            return

        print(f"Waiting for event processing: {attempt}/30")
        time.sleep(1)

    raise SystemExit("FAIL: The expected event ID did not appear in DynamoDB.")
    

if __name__ == "__main__":
    main()