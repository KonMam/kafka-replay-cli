import typer

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
):
    """Replay messages from Parquet into Kafka."""
    replay_parquet_to_kafka(
        input_path=input,
        topic=topic,
        bootstrap_servers=bootstrap_servers,
        throttle_ms=throttle_ms,
    )


if __name__ == "__main__":
    app()
