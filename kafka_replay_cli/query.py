import duckdb
import pandas as pd


def run_duckdb_query(input_path, sql, output_path=None, limit=None):
    con = duckdb.connect()
    con.execute(f"CREATE VIEW input AS SELECT * FROM '{input_path}'")

    if limit:
        sql = f"SELECT * FROM ({sql}) LIMIT {limit}"

    try:
        df = con.execute(sql).fetchdf()

        if output_path:
            if str(output_path).endswith(".csv"):
                df.to_csv(output_path, index=False)
            elif str(output_path).endswith(".json"):
                df.to_json(output_path, orient="records", lines=True)
            print(f"[✔] Query results written to {output_path}")
        else:
            print(df.to_string(index=False))

    except Exception as e:
        print(f"[!] Query failed: {e}")
    finally:
        con.close()
