provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  s3_use_path_style = true //use path localhost:4566/bukcet-name for s3

  endpoints { //routing listed service calls to Floci
    kinesis  = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
    s3       = "http://localhost:4566"
    sts      = "http://localhost:4566"
  }
}