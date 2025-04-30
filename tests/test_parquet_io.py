import os
import tempfile
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq

from kafka_replay_cli.schema import get_message_schema


def test_parquet_write_and_read():
    schema = get_message_schema()
    now = datetime.now()

    messages = [
        {
            "timestamp": now,
            "key": b"user-1",
            "value": b'{"event": "login"}',
            "partition": 0,
            "offset": 1,
        },
        {
            "timestamp": now,
            "key": b"user-2",
            "value": b'{"event": "purchase"}',
            "partition": 0,
            "offset": 2,
        },
    ]

    temp_path = os.path.join(tempfile.gettempdir(), "test_messages.parquet")

    try:
        batch = pa.record_batch(
            [
                [m["timestamp"] for m in messages],
                [m["key"] for m in messages],
                [m["value"] for m in messages],
                [m["partition"] for m in messages],
                [m["offset"] for m in messages],
            ],
            schema=schema,
        )

        pq.write_table(pa.Table.from_batches([batch]), temp_path)

        table = pq.read_table(temp_path)
        rows = table.to_pylist()

        assert len(rows) == 2
        assert rows[0]["key"] == b"user-1"
        assert rows[1]["value"] == b'{"event": "purchase"}'

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
