resource "aws_kinesis_stream" "playback" {  // aws_kinesis_stream is the resource type, playback is Terraforms internal label
  name             = "streampulse-playback" // stream name in Floci
  shard_count      = 1                      // Shard is a unit of stream capacity and partioning 
  retention_period = 24                     // 24-hour retenion window

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

resource "aws_dynamodb_table" "watch_progress" {
  name         = "streampulse-watch-progress"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "user_id"
  range_key = "video_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "video_id"
    type = "S"
  }
}

resource "aws_s3_bucket" "event_archive" {
  bucket = "streampulse-event-archive"
}