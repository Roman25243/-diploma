from __future__ import annotations

import argparse
import os
from typing import Iterable

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import Connection

from extensions import db
import models  # noqa: F401  # Ensure all tables are registered on db.metadata


DEFAULT_SOURCE_DATABASE_URL = os.environ.get('SOURCE_DATABASE_URL') or 'sqlite:///instance/cinema.db'
DEFAULT_TARGET_DATABASE_URL = os.environ.get('TARGET_DATABASE_URL') or os.environ.get('DATABASE_URL')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Copy all rows from a source database into a target database for CinemaBook.'
    )
    parser.add_argument(
        '--source',
        default=DEFAULT_SOURCE_DATABASE_URL,
        help='Source database URL. Default: SOURCE_DATABASE_URL or sqlite:///instance/cinema.db',
    )
    parser.add_argument(
        '--target',
        default=DEFAULT_TARGET_DATABASE_URL,
        help='Target database URL. Default: TARGET_DATABASE_URL or DATABASE_URL',
    )
    parser.add_argument(
        '--replace-target',
        action='store_true',
        help='Delete existing rows from the target database before copying.',
    )
    return parser.parse_args()


def target_has_data(connection: Connection) -> bool:
    inspector = inspect(connection)
    for table_name in inspector.get_table_names():
        row_count = connection.execute(text(f'SELECT COUNT(*) FROM {table_name}')).scalar_one()
        if row_count:
            return True
    return False


def clear_target_tables(connection: Connection) -> None:
    for table in reversed(db.metadata.sorted_tables):
        connection.execute(table.delete())


def copy_table(source_connection: Connection, target_connection: Connection, table) -> int:
    rows = source_connection.execute(select(table)).mappings().all()
    if not rows:
        return 0

    payload = [dict(row) for row in rows]
    target_connection.execute(table.insert(), payload)
    return len(payload)


def reset_postgres_sequences(connection: Connection) -> None:
    if connection.dialect.name != 'postgresql':
        return

    for table in db.metadata.sorted_tables:
        if not table.primary_key.columns:
            continue

        primary_key = next(iter(table.primary_key.columns))
        sequence_name = connection.execute(
            text('SELECT pg_get_serial_sequence(:table_name, :column_name)'),
            {'table_name': table.name, 'column_name': primary_key.name},
        ).scalar()
        if not sequence_name:
            continue

        max_value = connection.execute(select(func.max(primary_key))).scalar()
        if max_value is None:
            continue

        connection.execute(
            text('SELECT setval(:sequence_name, :sequence_value, true)'),
            {'sequence_name': sequence_name, 'sequence_value': int(max_value)},
        )


def main() -> int:
    args = parse_args()
    if not args.target:
        raise SystemExit('Target database URL is missing. Set DATABASE_URL or pass --target.')

    source_engine = create_engine(args.source)
    target_engine = create_engine(args.target)

    db.metadata.create_all(bind=target_engine)

    with source_engine.connect() as source_connection, target_engine.begin() as target_connection:
        if args.replace_target:
            clear_target_tables(target_connection)
        elif target_has_data(target_connection):
            raise SystemExit(
                'Target database already contains data. Re-run with --replace-target if you want to overwrite it.'
            )

        copied_rows = 0
        for table in db.metadata.sorted_tables:
            table_rows = copy_table(source_connection, target_connection, table)
            copied_rows += table_rows
            print(f'{table.name}: copied {table_rows} rows')

        reset_postgres_sequences(target_connection)

    print(f'Done. Copied {copied_rows} rows from {args.source} to {args.target}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())