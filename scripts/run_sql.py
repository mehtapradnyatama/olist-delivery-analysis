import argparse
from pathlib import Path

from analysis import PROJECT_ROOT, load_database, query_records, read_query, validate_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sql_file", type=Path, help="SQL file to run")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "dataset")
    args = parser.parse_args()

    sql_path = PROJECT_ROOT / args.sql_file
    with load_database(args.data_dir) as connection:
        source = query_records(connection, PROJECT_ROOT / "sql/00_source_data_quality.sql", args.data_dir)
        validate_source(source)
        query = read_query(sql_path, args.data_dir)
        connection.sql(query).show(max_rows=50, max_width=220)


if __name__ == "__main__":
    main()
