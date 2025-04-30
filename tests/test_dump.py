import tempfile
from datetime import datetime
from unittest.mock import MagicMock

import pyarrow.parquet as pq

from kafka_replay_cli.dump import dump_kafka_to_parquet


class FakeMessage:
    def __init__(self, key, value, ts, partition, offset):
        self._key = key
        self._value = value
        self._ts = ts
        self._partition = partition
        self._offset = offset

    def key(self): return self._key
    def value(self): return self._value
    def timestamp(self): return (0, int(self._ts.timestamp() * 1000))
    def partition(self): return self._partition
    def offset(self): return self._offset
    def error(self): return None


def test_dump_writes_parquet(monkeypatch):
    # Mock Kafka Consumer
    mock_consumer = MagicMock()
    now = datetime.now()
    fake_msgs = [
        FakeMessage(b'k1', b'v1', now, 0, 1),
        FakeMessage(b'k2', b'v2', now, 0, 2),
    ]

    mock_consumer.poll.side_effect = fake_msgs + [None, KeyboardInterrupt()]
    monkeypatch.setattr("kafka_replay_cli.dump.Consumer", lambda _: mock_consumer)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        output_path = tf.name

    dump_kafka_to_parquet(
        topic="test",
        bootstrap_servers="localhost:9092",
        output_path=output_path,
        max_messages=2,
        batch_size=1
    )

    table = pq.read_table(output_path)
    rows = table.to_pylist()

    assert len(rows) == 2
    assert rows[0]["key"] == b'k1'
    assert rows[1]["value"] == b'v2'
