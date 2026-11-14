resource "aws_api_gateway_rest_api" "playback" {
  name = "streampulse-playback-api"
}

resource "aws_api_gateway_resource" "playback" {
  rest_api_id = aws_api_gateway_rest_api.playback.id
  parent_id   = aws_api_gateway_rest_api.playback.root_resource_id
  path_part   = "playback"
}

resource "aws_api_gateway_resource" "playback_events" {
  rest_api_id = aws_api_gateway_rest_api.playback.id
  parent_id   = aws_api_gateway_resource.playback.id
  path_part   = "events"
}

resource "aws_api_gateway_method" "publish_playback" {
  rest_api_id   = aws_api_gateway_rest_api.playback.id
  resource_id   = aws_api_gateway_resource.playback_events.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "playback_ingest" {
  rest_api_id             = aws_api_gateway_rest_api.playback.id
  resource_id             = aws_api_gateway_resource.playback_events.id
  http_method             = aws_api_gateway_method.publish_playback.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.playback_ingest.invoke_arn
}

resource "aws_lambda_permission" "playback_api" {
  statement_id  = "AllowPlaybackApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.playback_ingest.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.playback.execution_arn}/local/POST/playback/events"
}

resource "aws_api_gateway_deployment" "playback" {
  rest_api_id = aws_api_gateway_rest_api.playback.id

  triggers = {
    redeployment = sha1(jsonencode([
      filesha256("${path.module}/playback_api.tf"),
      aws_api_gateway_integration.playback_ingest.id,
      aws_api_gateway_integration.playback_ingest.uri,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "playback_local" {
  rest_api_id   = aws_api_gateway_rest_api.playback.id
  deployment_id = aws_api_gateway_deployment.playback.id
  stage_name    = "local"
}

output "playback_events_url" {
  value = "http://127.0.0.1:4566/execute-api/${aws_api_gateway_rest_api.playback.id}/${aws_api_gateway_stage.playback_local.stage_name}/playback/events"
}