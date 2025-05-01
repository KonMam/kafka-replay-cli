# kafka-replay-cli Roadmap

## v0.3.x (Planned)

### Core Improvements

- Add `--batch-size` option to control replay batch size.
- Add `--dry-run-limit` option to adjust the number of preview messages during dry-run.
- Improve transform script validation:
    - Check for missing or incorrectly defined `transform` function.
    - Validate return type.
- Support offset-based filtering (`--partition`, `--offset-start`, `--offset-end`).
- Add CLI-level integration tests for full dump, replay, and transform flows.
- Warn when large throttle settings may cause excessive replay duration.

---

## Future (v0.4 or later)

### Potential Features

- Query-to-topic command (`query --output-topic`) for replaying query results directly into Kafka.
- Partitioned Parquet output in dump for handling large topics efficiently.
- Async Replay
- Optional dependency reduction for minimal installs.
- Batch replay optimizations.