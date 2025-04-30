import time

import pyarrow.parquet as pq
from confluent_kafka import Producer

from kafka_replay_cli.schema import get_message_schema


def replay_parquet_to_kafka(
    input_path: str,
    topic: str,
    bootstrap_servers: str,
    throttle_ms: int = 0,
):
    schema = get_message_schema()
    print(f"[+] Reading Parquet file from {input_path}")
    table = pq.read_table(input_path, schema=schema)

    print(f"[+] Preparing to replay {table.num_rows} messages to topic '{topic}'")
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    try:
        rows = table.to_pylist()
        for i, row in enumerate(rows):
            key = row["key"]
            value = row["value"]

            producer.produce(topic, key=key, value=value)

            if throttle_ms > 0 and i < len(rows) - 1:
                time.sleep(throttle_ms / 1000.0)

        producer.flush()
        print(f"[✔] Done. Replayed {len(rows)} messages to topic '{topic}'")

    except Exception as e:
        print(f"[!] Error during replay: {e}")
