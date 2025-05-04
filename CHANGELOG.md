# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Kafka tuning parameters in replay command
    - `acks`
    - `compression-type`
    - `producer-batch-size`
    - `linger-ms`
- Kafka tuning parameters in dump command
    - `fetch-max-bytes`

### Changed
- Pytest mocking now allows for any keyword arguments.
- Integration tests with Kafka tuning parameters.

### Removed

## [0.3.0] - 2025-05-01

### Added
- Partition filtering (`--partition`) and offset filtering (`--offset-start`, `--offset-end`) in replay command.
- Dynamic batch size control (`--batch-size`) in replay command.
- Dry-run message preview limit (`--dry-run-limit`) to control how many messages are displayed during dry-run mode.
- Full CLI-level integration tests for dump, replay, filtering, and transform flows.

### Changed
- Parquet dump now enforces --max-messages correctly at the per-message level.

---

## [0.2.0] - 2025-05-01

### Added
- `--dry-run` option for replay: preview what would be sent without producing messages.
- `--verbose` and `--quiet` flags to control CLI output verbosity.
- Detailed skip messages printed in verbose mode when using transform hooks.
- Warning when no messages are replayed after applying filters or transforms.
- Clear error raised when no messages match the specified filters.
- CLI version command: `kafka-replay-cli version`.
- Unit tests for dry-run, verbose, quiet, and transform skipping behavior.
- CLI integration test for version output.

---

## [0.1.1] - 2025-04-30

### Changed
- Updated README to reflect PyPI installation method.

---

## [0.1.0] - 2025-04-30

### Added
- Initial release.
- Kafka dump and replay commands.
- Timestamp and key filtering.
- Transform hook support.
- DuckDB query support.
- Unit tests for dump, replay, and filters.