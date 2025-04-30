from kafka_replay_cli.dump import dump_kafka_to_parquet

dump_kafka_to_parquet(
    topic="test-topic",
    bootstrap_servers="localhost:9092",
    output_path="test_messages.parquet",
    max_messages=10,
)
