import os
import tempfile
from datetime import datetime
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
