# kafka-replay-cli

`kafka-replay-cli` is a local-first CLI tool that lets developers dump Kafka topics to disk and replay them with filters. 


## Usage

pip install -r requirements.txt

## MVP Scope

| Component      | Description |
|----------------|-------------|
| Kafka Consumer | Reads from Kafka, buffers into batches |
| Parquet Writer | Writes batched Kafka messages as `RecordBatch` to `.parquet` |
| Kafka Producer | Reads from Parquet and publishes to Kafka |
| Throttle Logic | Adds delay between replays |
| CLI Interface  | `dump` and `replay` with `--input`, `--output`, `--topic`, etc. |
| Format         | Hardcoded to Parquet for now |