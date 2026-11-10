import sys

import boto3
from botocore.config import Config


ENDPOINT_URL = "http://localhost:4566"

SESSION = boto3.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

CLIENT_CONFIG = Config(
    connect_timeout=3,
    read_timeout=5,
    retries={"max_attempts": 0},
)


def main():
    checks = (
        ("s3", "list_buckets"),
        ("kinesis", "list_streams"),
        ("dynamodb", "list_tables"),
    )

    failures = 0

    for service, operation in checks:
        try:
            client = SESSION.client(
                service,
                endpoint_url=ENDPOINT_URL,
                config=CLIENT_CONFIG,
            )

            getattr(client, operation)()
            print(f"PASS: Python can reach {service}")

        except Exception as error:
            failures += 1
            print(f"FAIL: {service}: {error}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())