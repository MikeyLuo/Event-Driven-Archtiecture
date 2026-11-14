resource "aws_iam_role" "archive_worker" {
  name = "streampulse-archive-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_cloudwatch_log_group" "archive_worker" {
  name              = "/aws/lambda/streampulse-archive-worker"
  retention_in_days = 7
}

resource "aws_iam_role_policy" "archive_worker" {
  name = "streampulse-archive-worker-policy"
  role = aws_iam_role.archive_worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:DescribeStreamSummary",
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:ListShards",
        ]
        Resource = aws_kinesis_stream.playback.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.event_archive.arn}/playback/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.archive_worker.arn}:*"
      },
    ]
  })
}

resource "aws_lambda_function" "archive_worker" {
  function_name = "streampulse-archive-worker"
  role          = aws_iam_role.archive_worker.arn
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"

  filename         = "${path.module}/../build/archive_worker.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/archive_worker.zip")

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      FLOCI_ENDPOINT_URL   = "http://floci:4566"
      EVENT_ARCHIVE_BUCKET = aws_s3_bucket.event_archive.bucket
    }
  }

  depends_on = [aws_iam_role_policy.archive_worker]
}

resource "aws_lambda_event_source_mapping" "archive" {
  event_source_arn  = aws_kinesis_stream.playback.arn
  function_name     = aws_lambda_function.archive_worker.arn
  starting_position = "TRIM_HORIZON"
  batch_size        = 10
  enabled           = true
}