import importlib
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from confluent_kafka import Producer

from kafka_replay_cli.schema import get_message_schema


def replay_parquet_to_kafka(
    input_path: str,
    topic: str,
    bootstrap_servers: str,
    throttle_ms: int = 0,
    start_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None,
    key_filter: Optional[bytes] = None,
    transform: Optional[Callable[[dict], dict]] = None,
):
    schema = get_message_schema()
    print(f"[+] Reading Parquet file from {input_path}")
    table = pq.read_table(input_path, schema=schema)
    initial_count = table.num_rows

    if start_ts:
        table = table.filter(pc.greater_equal(table["timestamp"], pa.scalar(start_ts)))
    if end_ts:
        table = table.filter(pc.less_equal(table["timestamp"], pa.scalar(end_ts)))

    if key_filter:
        table = table.filter(pc.equal(table["key"], pa.scalar(key_filter)))

    print(f"[+] Filtered from {initial_count} to {table.num_rows} messages")

    print(f"[+] Preparing to replay {table.num_rows} messages to topic '{topic}'")
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    start_time = time.time()

    try:
        rows = table.to_pylist()
        for i, row in enumerate(rows):
            if transform:
                row = transform(row)
                if row is None:
                    print(f"[~] Skipping message {i} due to transform()")
                    continue

            key = row["key"]
            value = row["value"]

            producer.produce(topic, key=key, value=value)

            if throttle_ms > 0 and i < len(rows) - 1:
                time.sleep(throttle_ms / 1000.0)

        producer.flush()
        print(f"[✔] Done. Replayed {len(rows)} messages to topic '{topic}'")

        duration = time.time() - start_time
        if duration > 0:
            rate = len(rows) / duration
            print(f"[⏱] Replay rate: {rate:,.0f} messages/sec over {duration:.2f} seconds")

    except Exception as e:
        print(f"[!] Error during replay: {e}")


def load_transform_fn(script_path: Path):
    spec = importlib.util.spec_from_file_location("transform_mod", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "transform") or not callable(module.transform):
        raise ValueError(f"{script_path} must define a `transform(msg)` function")

    return module.transform
