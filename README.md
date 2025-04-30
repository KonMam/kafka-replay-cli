# kafka-replay-cli

A lightweight, local-first CLI tool for dumping and replaying Kafka messages using [Parquet](https://parquet.apache.org/) files. Built for observability, debugging, and safe testing of event streams.

---

## Features

- Dump Kafka topics into Parquet files
- Replay messages from Parquet back into Kafka
- Filter replays by timestamp range and key
- Optional throttling during replay (simulate timing)

---

## 📦 Installation

Install from PyPI:

```bash
pip install kafka-replay-cli
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

## 🛠️ Transform Messages Before Replay

You can modify, enrich, or skip Kafka messages during replay by passing a custom Python script that defines a `transform(msg)` function.

### Basic Example

**File:** `hooks/example_transform.py`

```python
def transform(msg):
    # Capitalize the value payload
    if msg["value"]:
        msg["value"] = msg["value"].upper()
    return msg
```

Then run:

```bash
kafka-replay-cli replay \
  --input messages.parquet \
  --topic replayed-topic \
  --transform-script hooks/example_transform.py
```

---

### Skip Messages

If your function returns `None`, the message will be skipped.

```python
def transform(msg):
    if b'"event":"login"' not in msg["value"]:
        return None
    return msg
```

---

### Message Format

Each `msg` is a dictionary with at least:

```python
{
  "timestamp": datetime,
  "key": bytes,
  "value": bytes,
  "partition": int,
  "offset": int
}
```

You may modify `key` and `value`, or add fields for logging/debugging.

---

## Querying Kafka Messages with DuckDB

You can run SQL directly on dumped Parquet files using the `query` command:

```bash
kafka-replay-cli query \
  --input test.parquet \
  --sql "SELECT timestamp, CAST(key AS VARCHAR) FROM input WHERE CAST(value AS VARCHAR) LIKE '%login%'"
```

> ⚠️ **Note**: Kafka `key` and `value` fields are stored as binary (`BLOB`) in the Parquet file for full fidelity.  
> To search or filter them using `LIKE`, you must explicitly cast them to `VARCHAR`.

---

### Output to file:

```bash
kafka-replay-cli query \
  --input test.parquet \
  --sql "SELECT key FROM input" \
  --output results.json
```

---

## License

MIT

---

## Maintainer

Konstantinas Mamonas  
Feel free to fork, open issues, or suggest improvements.