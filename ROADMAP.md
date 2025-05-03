# kafka-replay-cli Roadmap


## Future (v0.4 or later)

### Potential Features

- Query-to-topic command (`query --output-topic`) for replaying query results directly into Kafka.
- Partitioned Parquet output in dump for handling large topics efficiently.
- Async Replay
- Optional dependency reduction for minimal installs.
- Batch replay optimizations.
- Improve transform script validation:
    - Check for missing or incorrectly defined `transform` function.
    - Validate return type.
- Add warning when --throttle-ms exceeds a high value (e.g., > 5000 ms).
- Improve error message when Kafka broker connection fails.