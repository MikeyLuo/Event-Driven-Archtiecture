provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  s3_use_path_style = true //use path localhost:4566/bukcet-name for s3

  endpoints {
    kinesis        = "http://127.0.0.1:4566"
    dynamodb       = "http://127.0.0.1:4566"
    s3             = "http://127.0.0.1:4566"
    sts            = "http://127.0.0.1:4566"
    iam            = "http://127.0.0.1:4566"
    lambda         = "http://127.0.0.1:4566"
    cloudwatchlogs = "http://127.0.0.1:4566"
    apigateway     = "http://127.0.0.1:4566"
  }
}