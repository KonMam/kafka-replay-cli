import json
import subprocess
import time
from datetime import datetime

from confluent_kafka import Producer


def produce_test_messages(topic, bootstrap_servers, num_messages=2):
    p = Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "message.timeout.ms": 5000,
            "socket.timeout.ms": 5000,
        }
    )

    def acked(err, msg):
        if err:
            raise Exception(f"Failed to deliver message: {err}")

    for i in range(num_messages):
        key = f"cli-test-key-{i}"
        value = json.dumps({"event": f"cli-test-{i}", "ts": datetime.now().isoformat()})
        p.produce(topic, key=key.encode(), value=value.encode(), callback=acked)

    p.flush()


def test_cli_dump_and_dry_run_replay(tmp_path):
    # Parameters
    bootstrap_servers = "localhost:9092"
    topic = "cli-integration-test"
    parquet_output = tmp_path / "cli_test_output.parquet"

    # Step 1: Produce messages
    produce_test_messages(topic, bootstrap_servers)

    # Allow Kafka to process the messages
    time.sleep(2)

    # Step 2: Run dump command
    dump_cmd = [
        "kafka-replay-cli",
        "dump",
        "--topic",
        topic,
        "--output",
        str(parquet_output),
        "--bootstrap-servers",
        bootstrap_servers,
        "--max-messages",
        "2",
    ]

    result = subprocess.run(dump_cmd, capture_output=True, text=True, check=True)
    assert "Preparing to replay" not in result.stdout  # Should not see replay text
    assert parquet_output.exists()

    # Step 3: Run replay dry-run
    replay_cmd = [
        "kafka-replay-cli",
        "replay",
        "--input",
        str(parquet_output),
        "--topic",
        topic,
        "--dry-run",
        "--verbose",
    ]

    result = subprocess.run(replay_cmd, capture_output=True, text=True, check=True)
    assert "[Dry Run]" in result.stdout
    assert "cli-test-key-0" in result.stdout
    assert "cli-test-key-1" in result.stdout
