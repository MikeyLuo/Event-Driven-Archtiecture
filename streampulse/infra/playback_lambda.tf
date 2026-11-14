resource "aws_iam_role" "playback_worker" {
  name = "streampulse-playback-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "playback_worker" {
  name              = "/aws/lambda/streampulse-playback-worker"
  retention_in_days = 7
}

resource "aws_iam_role_policy" "playback_worker" {
  name = "streampulse-playback-worker-policy"
  role = aws_iam_role.playback_worker.id

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
          "kinesis:ListShards"
        ]
        Resource = aws_kinesis_stream.playback.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.watch_progress.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.playback_worker.arn}:*"
      }
    ]
  })
}

resource "aws_lambda_function" "playback_worker" {
  function_name = "streampulse-playback-worker"
  role          = aws_iam_role.playback_worker.arn

  runtime = "python3.12"
  handler = "handler.lambda_handler"

  filename = "${path.module}/../build/playback_worker.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../build/playback_worker.zip"
  )

  timeout     = 30
  memory_size = 256

  environment {
    variables = {
      FLOCI_ENDPOINT_URL   = "http://floci:4566"
      WATCH_PROGRESS_TABLE = aws_dynamodb_table.watch_progress.name
    }
  }

  depends_on = [
    aws_iam_role_policy.playback_worker,
    aws_cloudwatch_log_group.playback_worker
  ]
}

resource "aws_lambda_event_source_mapping" "playback" {
  event_source_arn = aws_kinesis_stream.playback.arn
  function_name    = aws_lambda_function.playback_worker.arn

  starting_position = "TRIM_HORIZON"
  batch_size        = 10
  enabled           = true

  depends_on = [
    aws_iam_role_policy.playback_worker
  ]
}