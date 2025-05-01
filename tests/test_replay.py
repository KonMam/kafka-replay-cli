import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kafka_replay_cli.replay import replay_parquet_to_kafka
from kafka_replay_cli.schema import get_message_schema


def create_test_parquet(path):
    schema = get_message_schema()
    now = datetime.now()
    batch = pa.record_batch(
        [
            [now, now],
            [b"k1", b"k2"],
            [b"v1", b"v2"],
            [0, 0],
            [1, 2],
        ],
        schema=schema,
    )
    pq.write_table(pa.Table.from_batches([batch]), path)


def test_replay_reads_parquet_and_produces(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet(tf.name)
        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="test-output",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
        )

    assert mock_producer.produce.call_count == 2
    args1 = mock_producer.produce.call_args_list[0][1]
    assert args1["key"] == b"k1"
    assert args1["value"] == b"v1"


def test_throttle_sleep_called(monkeypatch):
    mock_producer = MagicMock()
    mock_sleep = MagicMock()

    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)
    monkeypatch.setattr("time.sleep", mock_sleep)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet(tf.name)

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="test-throttled",
            bootstrap_servers="localhost:9092",
            throttle_ms=100,
        )

    # Should sleep once between 2 messages
    mock_sleep.assert_called_once_with(0.1)
    assert mock_producer.produce.call_count == 2


def test_replay_with_corrupted_file(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        tf.write(b"this is not a parquet file")
        tf_path = tf.name

    with pytest.raises(Exception):
        replay_parquet_to_kafka(
            input_path=tf_path,
            topic="corrupt-test",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
        )

    os.remove(tf_path)


def create_test_parquet_with_timestamps(path):
    schema = get_message_schema()
    now = datetime.now()
    msg1_time = now - timedelta(days=2)
    msg2_time = now

    batch = pa.record_batch(
        [
            [msg1_time, msg2_time],
            [b"k1", b"k2"],
            [b"v1", b"v2"],
            [0, 0],
            [1, 2],
        ],
        schema=schema,
    )
    pq.write_table(pa.Table.from_batches([batch]), path)


def test_replay_with_timestamp_filter(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_with_timestamps(tf.name)
        now = datetime.now()

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="filtered-topic",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
            start_ts=now - timedelta(hours=1),
            end_ts=now + timedelta(hours=1),
        )

    assert mock_producer.produce.call_count == 1
    args = mock_producer.produce.call_args_list[0][1]
    assert args["key"] == b"k2"
    assert args["value"] == b"v2"


def test_replay_with_key_filter(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_with_timestamps(tf.name)
        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="key-filtered",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
            key_filter=b"k1",
        )

    assert mock_producer.produce.call_count == 1
    args = mock_producer.produce.call_args_list[0][1]
    assert args["key"] == b"k1"
    assert args["value"] == b"v1"


def test_replay_with_key_and_timestamp_filter(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    # Two rows:
    # - msg1: too early, wrong timestamp but key matches
    # - msg2: good timestamp, but wrong key
    schema = get_message_schema()
    now = datetime.now()
    msg1_time = now - timedelta(days=2)
    msg2_time = now

    batch = pa.record_batch(
        [
            [msg1_time, msg2_time],
            [b"target", b"other"],
            [b"v1", b"v2"],
            [0, 0],
            [1, 2],
        ],
        schema=schema,
    )

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        pq.write_table(pa.Table.from_batches([batch]), tf.name)

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="combo-filtered",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
            start_ts=now - timedelta(hours=1),
            end_ts=now + timedelta(hours=1),
            key_filter=b"target",
        )

    assert mock_producer.produce.call_count == 0


def test_replay_with_transform_skips_and_modifies(monkeypatch):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    schema = get_message_schema()
    now = datetime.now()
    batch = pa.record_batch(
        [
            [now, now],  # timestamps
            [b"k1", b"k2"],  # keys
            [b"v1", b"v2"],  # values
            [0, 0],  # partitions
            [1, 2],  # offsets
        ],
        schema=schema,
    )

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        pq.write_table(pa.Table.from_batches([batch]), tf.name)

        def mock_transform(msg):
            if msg["value"] == b"v1":
                return None
            msg["value"] = b"CHANGED"
            return msg

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="transform-test",
            bootstrap_servers="localhost:9092",
            throttle_ms=0,
            transform=mock_transform,
        )

    assert mock_producer.produce.call_count == 1
    args = mock_producer.produce.call_args_list[0][1]
    assert args["key"] == b"k2"
    assert args["value"] == b"CHANGED"


def create_test_parquet_for_dry_run(path):
    schema = get_message_schema()
    now = datetime.now()
    batch = pa.record_batch(
        [
            [now, now],  # timestamps
            [b"key1", b"key2"],  # keys
            [b"value1", b"value2"],  # values
            [0, 0],  # partitions
            [1, 2],  # offsets
        ],
        schema=schema,
    )
    pq.write_table(pa.Table.from_batches([batch]), path)


def test_replay_dry_run(monkeypatch, capsys):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_for_dry_run(tf.name)

        replay_parquet_to_kafka(
            input_path=tf.name, topic="dry-run-test", bootstrap_servers="localhost:9092", dry_run=True
        )

    assert mock_producer.produce.call_count == 0

    captured = capsys.readouterr()
    assert "[Dry Run] Would replay: key=key1" in captured.out
    assert "[Dry Run] Would replay: key=key2" in captured.out
    assert "messages would have been replayed" in captured.out


def test_replay_dry_run_with_transform(monkeypatch, capsys):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_for_dry_run(tf.name)

        def test_transform(msg):
            if msg["key"] == b"key1":
                return None  # Skip first message
            return msg

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="dry-run-transform-test",
            bootstrap_servers="localhost:9092",
            dry_run=True,
            transform=test_transform,
        )

    assert mock_producer.produce.call_count == 0

    captured = capsys.readouterr()

    assert "[Dry Run] Would replay: key=key2" in captured.out
    assert "[Dry Run] Would replay: key=key1" not in captured.out
    assert "messages would have been replayed" in captured.out


def test_replay_dry_run_quiet(monkeypatch, capsys):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_for_dry_run(tf.name)

        replay_parquet_to_kafka(
            input_path=tf.name, topic="quiet-test", bootstrap_servers="localhost:9092", dry_run=True, quiet=True
        )

    assert mock_producer.produce.call_count == 0

    captured = capsys.readouterr()

    assert "[Dry Run] Would replay" not in captured.out
    assert captured.out == ""


def test_replay_dry_run_verbose_transform(monkeypatch, capsys):
    mock_producer = MagicMock()
    monkeypatch.setattr("kafka_replay_cli.replay.Producer", lambda _: mock_producer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        create_test_parquet_for_dry_run(tf.name)

        def transform_skip_first(msg):
            if msg["key"] == b"key1":
                return None
            return msg

        replay_parquet_to_kafka(
            input_path=tf.name,
            topic="verbose-test",
            bootstrap_servers="localhost:9092",
            dry_run=True,
            transform=transform_skip_first,
            verbose=True,
        )

    assert mock_producer.produce.call_count == 0

    captured = capsys.readouterr()

    assert "Skipping message 0 due to transform()" in captured.out
    assert "[Dry Run] Would replay: key=key2" in captured.out
    assert "[Dry Run] Would replay: key=key1" not in captured.out
