output "playback_stream_name" {
  description = "Kinesis stream receiving playback events."
  value       = aws_kinesis_stream.playback.name // Get the name attribute of the Kinsesis resource we labeled playback
}

output "watch_progress_table_name" {
  description = "DynamoDB table storing user watch progress."
  value       = aws_dynamodb_table.watch_progress.name
}

output "event_archive_bucket_name" {
  description = "S3 bucket storing archived playback events."
  value       = aws_s3_bucket.event_archive.bucket
}