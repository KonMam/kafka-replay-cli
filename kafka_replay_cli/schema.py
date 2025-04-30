import pyarrow as pa


def get_message_schema():
    return pa.schema(
        [
            ("timestamp", pa.timestamp("ms")),
            ("key", pa.binary()),
            ("value", pa.binary()),
            ("partition", pa.int32()),
            ("offset", pa.int64()),
        ]
    )
