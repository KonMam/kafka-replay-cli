import json
import subprocess
import time
import uuid
from datetime import datetime, timedelta

import duckdb
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
    bootstrap_servers = "localhost:9092"
    topic = f"cli-integration-test-{uuid.uuid4()}"
    parquet_output = tmp_path / "cli_test_output.parquet"

    produce_test_messages(topic, bootstrap_servers)

    time.sleep(2)

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
    assert "Preparing to replay" not in result.stdout
    assert parquet_output.exists()

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


def test_cli_replay_start_ts(tmp_path):
    bootstrap_servers = "localhost:9092"
    topic = f"cli-integration-startts-{uuid.uuid4()}"
    parquet_output = tmp_path / "cli_test_output.parquet"

    p = Producer({"bootstrap.servers": bootstrap_servers})

    now = datetime.now()

    p.produce(topic, key=b"old", value=b"value-old", timestamp=int((now - timedelta(days=1)).timestamp() * 1000))

    p.produce(topic, key=b"new", value=b"value-new", timestamp=int((now + timedelta(seconds=1)).timestamp() * 1000))

    p.flush()

    time.sleep(2)

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

    subprocess.run(dump_cmd, capture_output=True, text=True, check=True)

    start_ts = (now + timedelta(seconds=0.5)).isoformat()

    replay_cmd = [
        "kafka-replay-cli",
        "replay",
        "--input",
        str(parquet_output),
        "--topic",
        topic,
        "--start-ts",
        start_ts,
        "--dry-run",
    ]

    result = subprocess.run(replay_cmd, capture_output=True, text=True, check=True)
    stdout = result.stdout

    assert "key=new" in stdout
    assert "key=old" not in stdout


def test_cli_replay_key_filter(tmp_path):
    bootstrap_servers = "localhost:9092"
    topic = f"cli-integration-keyfilter-{uuid.uuid4()}"
    parquet_output = tmp_path / "cli_test_output.parquet"

    p = Producer({"bootstrap.servers": bootstrap_servers})

    p.produce(topic, key=b"key-match", value=b"value1")
    p.produce(topic, key=b"key-skip", value=b"value2")

    p.flush()
    time.sleep(2)

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

    subprocess.run(dump_cmd, capture_output=True, text=True, check=True)

    replay_cmd = [
        "kafka-replay-cli",
        "replay",
        "--input",
        str(parquet_output),
        "--topic",
        topic,
        "--key-filter",
        "key-match",
        "--dry-run",
    ]

    result = subprocess.run(replay_cmd, capture_output=True, text=True, check=True)
    stdout = result.stdout

    assert "key=key-match" in stdout
    assert "key=key-skip" not in stdout


def test_cli_replay_partition_offset_filter_dynamic(tmp_path):
    bootstrap_servers = "localhost:9092"
    topic = f"cli-integration-partitionoffset-{uuid.uuid4()}"
    parquet_output = tmp_path / "cli_test_partitionoffset_output.parquet"

    p = Producer({"bootstrap.servers": bootstrap_servers})

    p.produce(topic, key=b"key-match", value=b"value1", partition=0)
    p.produce(topic, key=b"key-other", value=b"value2", partition=0)
    p.produce(topic, key=b"key-match", value=b"value3", partition=0)

    p.flush()
    time.sleep(2)

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
        "3",
    ]

    subprocess.run(dump_cmd, capture_output=True, text=True, check=True)

    con = duckdb.connect()
    df = con.execute(f'SELECT "key", "partition", "offset" FROM "{parquet_output}"').df()
    print(df)
    target_offsets = []
    for _, row in df.iterrows():
        row_key = row["key"]
        if isinstance(row_key, bytearray):
            row_key = bytes(row_key)

        if row_key == b"key-match":
            target_offsets.append(row["offset"])

    assert target_offsets, "No matching offsets found for key-match"

    offset_start = max(target_offsets)

    replay_cmd = [
        "kafka-replay-cli",
        "replay",
        "--input",
        str(parquet_output),
        "--topic",
        topic,
        "--partition",
        "0",
        "--offset-start",
        str(offset_start),
        "--dry-run",
    ]

    result = subprocess.run(replay_cmd, capture_output=True, text=True, check=True)
    stdout = result.stdout

    assert "key=key-match" in stdout
    assert "key=key-other" not in stdout


def test_cli_replay_with_transform(tmp_path):
    bootstrap_servers = "localhost:9092"
    topic = f"cli-integration-transform-{uuid.uuid4()}"
    parquet_output = tmp_path / "cli_test_transform_output.parquet"
    transform_script = tmp_path / "transform_skip.py"

    p = Producer({"bootstrap.servers": bootstrap_servers})

    p.produce(topic, key=b"keep-1", value=b"value-keep")
    p.produce(topic, key=b"skip-me", value=b"value-skip")
    p.produce(topic, key=b"keep-2", value=b"value-keep2")

    p.flush()
    time.sleep(3)

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
        "3",
    ]

    subprocess.run(dump_cmd, capture_output=True, text=True, check=True)

    transform_script.write_text(
        """
def transform(msg):
    if msg["key"].startswith(b"skip"):
        return None
    return msg
"""
    )

    replay_cmd = [
        "kafka-replay-cli",
        "replay",
        "--input",
        str(parquet_output),
        "--topic",
        topic,
        "--transform-script",
        str(transform_script),
        "--dry-run",
        "--verbose",
    ]

    result = subprocess.run(replay_cmd, capture_output=True, text=True, check=True)
    stdout = result.stdout

    assert "key=skip-me" not in stdout
    assert "key=keep-1" in stdout
    assert "key=keep-2" in stdout
    assert "[~] Skipping message" in stdout
