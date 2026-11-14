resource "aws_iam_role" "playback_ingest" {
  name = "streampulse-playback-ingest-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_cloudwatch_log_group" "playback_ingest" {
  name              = "/aws/lambda/streampulse-playback-ingest"
  retention_in_days = 7
}

resource "aws_iam_role_policy" "playback_ingest" {
  name = "streampulse-playback-ingest-policy"
  role = aws_iam_role.playback_ingest.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["kinesis:PutRecord"]
        Resource = aws_kinesis_stream.playback.arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.playback_ingest.arn}:*"
      }
    ]
  })
}

resource "aws_lambda_function" "playback_ingest" {
  function_name = "streampulse-playback-ingest"
  role          = aws_iam_role.playback_ingest.arn
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"

  filename         = "${path.module}/../build/playback_ingest.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/playback_ingest.zip")

  timeout     = 20
  memory_size = 256

  environment {
    variables = {
      FLOCI_ENDPOINT_URL   = "http://floci:4566"
      PLAYBACK_STREAM_NAME = aws_kinesis_stream.playback.name
    }
  }

  depends_on = [aws_iam_role_policy.playback_ingest]
}