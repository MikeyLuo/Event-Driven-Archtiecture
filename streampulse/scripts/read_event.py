import argparse
import json
import time

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
    parser = argparse.ArgumentParser(
        description="Read one specific playback record from Kinesis."
    )

    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--sequence-number", required=True)

    args = parser.parse_args()

    response = kinesis.get_shard_iterator(
        StreamName=STREAM_NAME,
        ShardId=args.shard_id,
        ShardIteratorType="AT_SEQUENCE_NUMBER", # A shard iterator is a token telling Kinesis where to start reading within a shard
        StartingSequenceNumber=args.sequence_number,
    )

    shard_iterator = response["ShardIterator"]

    for attempt in range(1, 11):
        response = kinesis.get_records( # requests records from the shards location
            ShardIterator=shard_iterator,
            Limit=10,
        )

        for record in response["Records"]:
            if record["SequenceNumber"] == args.sequence_number:
                event = json.loads(record["Data"].decode("utf-8"))

                print("Found the requested record:")
                print(f"Partition key: {record['PartitionKey']}")
                print(f"Sequence number: {record['SequenceNumber']}")
                print(json.dumps(event, indent=2))

                return

        shard_iterator = response.get("NextShardIterator")

        if not shard_iterator:
            break

        print(f"Record not returned yet; poll {attempt}/10.")
        time.sleep(1)

    raise SystemExit(
        "Record was not found within the polling limit. "
        "Check the shard ID and sequence number."
    )


if __name__ == "__main__":
    main()