# kafka-replay-cli

A lightweight, CLI tool for dumping and replaying Kafka messages using [Parquet](https://parquet.apache.org/) files. Built for observability, debugging, and safe testing of event streams.

**Use it to:**
- Safely test event streams without impacting production.
- Debug complex Kafka flows by replaying exact message sets.
- Apply filters, transformations, and throttling for precise control.

---

## Features

- Dump Kafka topics into Parquet files
- Replay messages from Parquet back into Kafka
- Filter replays by timestamp range and key
- Optional throttling during replay
- Apply custom transform hooks to modify or skip messages
- Preview replays without sending messages using `--dry-run`
- Control output verbosity with `--verbose` and `--quiet`
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

### Advanced Dump Settings

```bash
--fetch-max-bytes 1000000   # Max bytes to fetch from broker per poll
```

---

### Replay messages from a Parquet file

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --bootstrap-servers localhost:9092 \
  --throttle-ms 100 
```

### Advanced Producer Settings

You can fine-tune how the replay produces messages to Kafka:

```bash
--acks all                 # Wait for all replicas to acknowledge (0, 1, or all)
--compression-type gzip    # Compress messages (gzip, snappy, lz4, zstd)
--linger-ms 10             # Delay to batch more messages (in milliseconds)
--producer-batch-size 5000 # Max batch size in bytes for Kafka producer
```

---

### Preview messages without sending (`--dry-run`)

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --dry-run
```

By default, shows up to 5 sample messages that would be replayed.
Use `--dry-run-limit` to adjust the number of preview messages.

```bash
--dry-run-limit 10
```

### Adjust verbosity

```bash
--verbose  # Show detailed logs, including skipped messages
--quiet    # Suppress all output except errors and final summary
```

Example:

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --dry-run \
  --verbose
```

---

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

### Add partition and offset filters

```bash
--partition 1            # Only replay messages from partition 1
--offset-start 1000      # Replay offsets >= 1000
--offset-end 2000        # Replay offsets <= 2000
```

Example:

```bash
kafka-replay-cli replay \
  --input test.parquet \
  --topic replayed-topic \
  --partition 0 \
  --offset-start 100 \
  --offset-end 200
```

---

### Control batch size

```bash
--batch-size 500
```

Controls how many messages are processed per batch during replay.

---

## Transform Messages Before Replay

You can modify, enrich, or skip Kafka messages during replay by passing a custom Python script that defines a `transform(msg)` function.

### Basic Example

File: `hooks/example_transform.py`

```python
def transform(msg):
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

If your function returns `None`, the message will be skipped.  
Use `--verbose` to see skip notices.

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

**Note:** Kafka `key` and `value` are stored as binary (BLOB) for fidelity.  
To search or filter them, use `CAST(... AS VARCHAR)`.

---

### Output query results to file

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

Use:

```bash
kafka-replay-cli version
```

to check the installed version.

---

## Roadmap

See the [ROADMAP](./ROADMAP.md) for upcoming features and plans.