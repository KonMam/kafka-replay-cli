from kafka_replay_cli.replay import replay_parquet_to_kafka

replay_parquet_to_kafka(
    input_path="test_messages.parquet",
    topic="replayed-topic",
    bootstrap_servers="localhost:9092",
    throttle_ms=100,
)
