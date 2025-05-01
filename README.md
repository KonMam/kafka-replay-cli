# kafka-replay-cli

A lightweight, CLI tool for dumping and replaying Kafka messages using [Parquet](https://parquet.apache.org/) files. Built for observability, debugging, and safe testing of event streams.

---

## Features

- Dump Kafka topics into Parquet files
- Replay messages from Parquet back into Kafka
- Filter replays by timestamp range and key
- Optional throttling during replay
- Apply custom transform hooks to modify or skip messages
- Query message dumps with DuckDB SQL

---

## Installation

```bash
pip install kafka-replay-cli
```

Requires Python 3.8 or newer.

---

## Kafka Broker Requirements

You must have access to a running Kafka broker.

By default, the CLI will attempt to connect to `localhost:9092`, but you can specify **any broker** using the `--bootstrap-servers` option:

```bash
--bootstrap-servers my.kafka.broker:9092
```

---

## Usage

### Dump messages from a topic to Parquet

```bash
kafka-replay-cli dump \
  --topic test-topic \
  --output test.parquet \
  --bootstrap-servers localhost:9092 \
  --max-messages 1000
```

### Replay messages from a Parquet file

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --bootstrap-servers localhost:9092 \
  --throttle-ms 100
```

### Add timestamp and key filters

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --start-ts "2024-01-01T00:00:00Z" \
  --end-ts "2024-01-02T00:00:00Z" \
  --key-filter "user-123"
```

---

## Transform Messages Before Replay

You can modify, enrich, or skip Kafka messages during replay by passing a custom Python script that defines a `transform(msg)` function.

### Basic Example

File: `hooks/example_transform.py`

```python
def transform(msg):
    # Capitalize the value payload
    if msg["value"]:
        msg["value"] = msg["value"].upper()
    return msg
```

Run with:

```bash
kafka-replay-cli replay \
  --input messages.parquet \
  --topic replayed-topic \
  --transform-script hooks/example_transform.py
```

### Skip Messages

If your function returns `None`, the message will be skipped:

```python
def transform(msg):
    if b'"event":"login"' not in msg["value"]:
        return None
    return msg
```

### Message Format

Each `msg` is a dictionary:

```python
{
  "timestamp": datetime,
  "key": bytes,
  "value": bytes,
  "partition": int,
  "offset": int
}
```

You can modify `key` and `value`, or add additional fields.

---

## Query Messages with DuckDB

Run SQL queries directly on dumped Parquet files:

```bash
kafka-replay-cli query \
  --input test.parquet \
  --sql "SELECT timestamp, CAST(key AS VARCHAR) FROM input WHERE CAST(value AS VARCHAR) LIKE '%login%'"
```

Note: Kafka `key` and `value` are stored as binary (BLOB) for fidelity.  
To search or filter them, use `CAST(... AS VARCHAR)`.

### Output to file

```bash
kafka-replay-cli query \
  --input test.parquet \
  --sql "SELECT key FROM input" \
  --output results.json
```

---

## License

MIT

This project is not affiliated with or endorsed by the Apache Kafka project.

---

## Maintainer

Konstantinas Mamonas

Feel free to fork, open issues, or suggest improvements.

---

## Version

Use `kafka-replay-cli --version` to check the installed version.

---

## Roadmap

See the [ROADMAP](./ROADMAP.md) for upcoming features and plans.