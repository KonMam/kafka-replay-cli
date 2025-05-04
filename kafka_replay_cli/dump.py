from datetime import datetime
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq
from confluent_kafka import Consumer, KafkaError

from kafka_replay_cli.schema import get_message_schema
from kafka_replay_cli.utils import validate_positive


def dump_kafka_to_parquet(
    topic: str,
    bootstrap_servers: str,
    output_path: str,
    max_messages: Optional[int] = None,
    batch_size: int = 1000,
    from_beginning: bool = True,
    fetch_max_bytes: int = 52428800,
):
    validate_positive(batch_size, "Batch size")
    validate_positive(max_messages, "Max messages")
    validate_positive(fetch_max_bytes, "Fetch max bytes")

    consumer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": "kafka-replay-dumper",
        "auto.offset.reset": "earliest" if from_beginning else "latest",
        "enable.auto.commit": False,
        "fetch.max.bytes": fetch_max_bytes,
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])
    print(f"[+] Subscribed to topic '{topic}'")

    collected = []
    written_count = 0
    schema = get_message_schema()
    writer = None

    try:
        no_message_count = 0
        max_no_message_count = 10

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                no_message_count += 1
                if no_message_count >= max_no_message_count:
                    print("[!] No new messages received for 10 seconds. Exiting early.")
                    break
                continue
            no_message_count = 0

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise msg.error()

            record = {
                "timestamp": datetime.fromtimestamp(msg.timestamp()[1] / 1000),
                "key": msg.key(),
                "value": msg.value(),
                "partition": msg.partition(),
                "offset": msg.offset(),
            }

            collected.append(record)
            written_count += 1

            if max_messages and written_count >= max_messages:
                break

            if len(collected) >= batch_size:
                print(f"[=] Writing batch of {len(collected)} to {output_path}")
                batch = to_record_batch(collected, schema)
                if writer is None:
                    writer = pq.ParquetWriter(output_path, schema)
                writer.write_table(pa.Table.from_batches([batch]))
                collected = []

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")

    finally:
        if collected:
            print(f"[=] Writing remaining {len(collected)} messages to {output_path} before exit")
            batch = to_record_batch(collected, schema)
            if writer is None:
                writer = pq.ParquetWriter(output_path, schema)
            writer.write_table(pa.Table.from_batches([batch]))

        if writer:
            writer.close()
        consumer.close()
        print(f"[✔] Done. Written {written_count} messages to {output_path}")


def to_record_batch(messages: list[dict], schema: pa.Schema) -> pa.RecordBatch:
    return pa.record_batch(
        [
            [m["timestamp"] for m in messages],
            [m["key"] for m in messages],
            [m["value"] for m in messages],
            [m["partition"] for m in messages],
            [m["offset"] for m in messages],
        ],
        schema=schema,
    )
