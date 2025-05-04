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
from kafka_replay_cli.utils import validate_positive


def replay_parquet_to_kafka(
    input_path: str,
    topic: str,
    bootstrap_servers: str,
    throttle_ms: int = 0,
    start_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None,
    key_filter: Optional[bytes] = None,
    transform: Optional[Callable[[dict], dict]] = None,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    batch_size: int = 1000,
    dry_run_limit: int = 5,
    partition: Optional[int] = None,
    offset_start: Optional[int] = None,
    offset_end: Optional[int] = None,
    acks: str = "all",
    compression_type: Optional[str] = None,
    producer_batch_size: int = 16384,
    linger_ms: int = 0,
):
    schema = get_message_schema()

    if not quiet:
        print(f"[+] Reading Parquet file from {input_path}")
    table = pq.read_table(input_path, schema=schema)
    initial_count = table.num_rows

    if start_ts:
        table = table.filter(pc.greater_equal(table["timestamp"], pa.scalar(start_ts)))
    if end_ts:
        table = table.filter(pc.less_equal(table["timestamp"], pa.scalar(end_ts)))

    if key_filter:
        table = table.filter(pc.equal(table["key"], pa.scalar(key_filter)))

    if partition:
        table = table.filter(pc.equal(table["partition"], pa.scalar(partition)))

    if offset_start:
        table = table.filter(pc.greater_equal(table["offset"], pa.scalar(offset_start)))

    if offset_end:
        table = table.filter(pc.less_equal(table["offset"], pa.scalar(offset_end)))

    if table.num_rows == 0:
        raise ValueError("No messages match the specified filters. Nothing to replay.")

    if not quiet:
        print(f"[+] Filtered from {initial_count} to {table.num_rows} messages")
        print(f"[+] Preparing to replay {table.num_rows} messages to topic '{topic}'")

    valid_acks = {"0", "1", "all"}
    if acks and acks not in valid_acks:
        raise ValueError(f"Invalid value for --acks. Must be one of {valid_acks}.")

    valid_compressions = {"gzip", "snappy", "lz4", "zstd"}
    if compression_type and compression_type not in valid_compressions:
        raise ValueError(f"Invalid compression type. Must be one of {valid_compressions}.")

    validate_positive(producer_batch_size, "Producer batch size")

    if linger_ms < 0:
        raise ValueError("linger_ms cannot be negative.")

    conf = {
        "bootstrap.servers": bootstrap_servers,
        "acks": acks,
        "batch.size": producer_batch_size,
        "linger.ms": linger_ms,
    }

    if compression_type:
        conf["compression.type"] = compression_type

    producer = Producer(**conf)

    start_time = time.time()

    def chunked(iterable, n):
        for idx in range(0, len(iterable), n):
            yield iterable[idx : idx + n]

    try:
        rows = table.to_pylist()
        sent = 0
        batch_num = 0

        for batch in chunked(rows, batch_size):
            batch_num += 1
            if verbose and not quiet:
                print(f"[=] Starting batch {batch_num} with {len(batch)} messages")

            for i, row in enumerate(batch):
                if transform:
                    row = transform(row)
                    if row is None:
                        if verbose and not quiet:
                            print(f"[~] Skipping message {i} in batch {batch_num} due to transform()")
                        continue

                if dry_run:
                    if sent < dry_run_limit and not quiet:
                        key_display = row["key"].decode(errors="replace") if row["key"] else "None"
                        value_display = row["value"].decode(errors="replace") if row["value"] else "None"
                        print(f"[Dry Run] Would replay: key={key_display} value={value_display}")
                    sent += 1
                    continue

                key = row["key"]
                value = row["value"]

                producer.produce(topic, key=key, value=value)
                sent += 1

                if throttle_ms > 0 and i < len(batch) - 1:
                    time.sleep(throttle_ms / 1000.0)

            if not dry_run:
                producer.flush()
                if verbose and not quiet:
                    print(f"[=] Finished batch {batch_num}, sent {sent} messages so far.")

        if not dry_run:
            print(f"[✔] Done. Replayed {sent} messages to topic '{topic}'")
        else:
            if not quiet:
                print(f"[Dry Run] {sent} messages would have been replayed.")

        if sent == 0:
            print("[!] No messages were replayed after applying filters and transform.")

        duration = time.time() - start_time
        if duration > 0 and not quiet:
            rate = sent / duration
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
