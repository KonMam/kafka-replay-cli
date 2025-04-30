from typing import Optional

import typer
from dateutil import parser as dateparser

from kafka_replay_cli.dump import dump_kafka_to_parquet
from kafka_replay_cli.replay import replay_parquet_to_kafka

app = typer.Typer(help="Kafka Replay CLI: Dump and replay Kafka messages using Parquet.")


@app.command()
def dump(
    topic: str = typer.Option(..., help="Kafka topic to consume from"),
    bootstrap_servers: str = typer.Option("localhost:9092", help="Kafka bootstrap server"),
    output: str = typer.Option(..., help="Output Parquet file path"),
    max_messages: int = typer.Option(None, help="Maximum number of messages to dump"),
    batch_size: int = typer.Option(1000, help="Number of messages per Parquet batch"),
    from_beginning: bool = typer.Option(True, help="Start consuming from beginning"),
):
    """Dump Kafka messages to a Parquet file."""
    dump_kafka_to_parquet(
        topic=topic,
        bootstrap_servers=bootstrap_servers,
        output_path=output,
        max_messages=max_messages,
        batch_size=batch_size,
        from_beginning=from_beginning,
    )


@app.command()
def replay(
    input: str = typer.Option(..., help="Input Parquet file"),
    topic: str = typer.Option(..., help="Kafka topic to replay into"),
    bootstrap_servers: str = typer.Option("localhost:9092", help="Kafka bootstrap server"),
    throttle_ms: int = typer.Option(0, help="Delay between messages in milliseconds"),
    start_ts: Optional[str] = typer.Option(None, help="Replay messages after this UTC ISO timestamp"),
    end_ts: Optional[str] = typer.Option(None, help="Replay messages before this UTC ISO timestamp"),
    key_filter: Optional[str] = typer.Option(None, help="Only replay messages where the key matches this value"),
):
    """Replay messages from Parquet into Kafka."""

    start = dateparser.parse(start_ts) if start_ts else None
    end = dateparser.parse(end_ts) if end_ts else None

    replay_parquet_to_kafka(
        input_path=input,
        topic=topic,
        bootstrap_servers=bootstrap_servers,
        throttle_ms=throttle_ms,
        start_ts=start,
        end_ts=end,
        key_filter=key_filter.encode() if key_filter else None,
    )


if __name__ == "__main__":
    app()
