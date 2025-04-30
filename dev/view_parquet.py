import os
import sys

import duckdb


def view_parquet(file_path: str, limit: int = 20):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        sys.exit(1)

    print(f"[+] Previewing {file_path} using DuckDB (limit {limit})\n")

    con = duckdb.connect()
    try:
        query = f"SELECT * FROM '{file_path}' LIMIT {limit}"
        result = con.execute(query).fetchdf()
        print(result.to_string(index=False))
    except Exception as e:
        print(f"[!] Failed to read: {e}")
    finally:
        con.close()


view_parquet("test_messages.parquet")
