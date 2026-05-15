import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text


BASE_DIR = Path(__file__).resolve().parents[1]
SQLITE_DB = BASE_DIR / "instance" / "site.db"
DOTENV_PATH = BASE_DIR / ".env"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models import db


def normalize_database_url(database_url):
    if database_url and database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    if database_url and database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def sqlite_columns(connection, table_name):
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return [row[1] for row in rows]


def table_primary_keys(inspector, table_name):
    return inspector.get_pk_constraint(table_name).get("constrained_columns") or []


def row_exists(target_connection, table_name, primary_keys, row):
    if not primary_keys:
        return False

    where_sql = " AND ".join([f'"{key}" = :pk_{key}' for key in primary_keys])
    params = {f"pk_{key}": row[key] for key in primary_keys}
    result = target_connection.execute(
        text(f'SELECT 1 FROM "{table_name}" WHERE {where_sql} LIMIT 1'),
        params,
    ).first()
    return result is not None


def insert_row(target_connection, table_name, columns, row):
    quoted_columns = ", ".join([f'"{column}"' for column in columns])
    placeholders = ", ".join([f":{column}" for column in columns])
    params = {column: row[column] for column in columns}
    target_connection.execute(
        text(f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'),
        params,
    )


def main():
    load_dotenv(DOTENV_PATH)

    if not SQLITE_DB.exists():
        raise SystemExit(f"SQLite database not found: {SQLITE_DB}")

    database_url = normalize_database_url(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise SystemExit("DATABASE_URL is not set. Add your PostgreSQL URL to .env or hosting env vars first.")

    if database_url.startswith("sqlite"):
        raise SystemExit("DATABASE_URL points to SQLite. Use a persistent PostgreSQL DATABASE_URL for deploy-safe sync.")

    if "railway.internal" in database_url:
        raise SystemExit(
            "DATABASE_URL is using Railway's private internal host (postgres.railway.internal). "
            "That works only inside Railway. For local sync, use Railway's public TCP/proxy URL "
            "like postgresql://USER:PASSWORD@switchyard.proxy.rlwy.net:PORT/railway."
        )

    os.environ["DATABASE_URL"] = database_url

    print("Creating missing target tables with metadata.create_all(check only; no drop/delete)...")
    target_engine = create_engine(database_url)
    db.metadata.create_all(target_engine)

    sqlite_connection = sqlite3.connect(SQLITE_DB)
    sqlite_connection.row_factory = sqlite3.Row
    target_inspector = inspect(target_engine)
    target_tables = set(target_inspector.get_table_names())

    inserted_total = 0
    skipped_total = 0

    try:
        with target_engine.begin() as target_connection:
            for table in db.metadata.sorted_tables:
                table_name = table.name
                if table_name not in target_tables:
                    print(f"Skipping missing target table: {table_name}")
                    continue

                try:
                    source_columns = sqlite_columns(sqlite_connection, table_name)
                except sqlite3.OperationalError:
                    print(f"Skipping missing source table: {table_name}")
                    continue

                target_columns = {column["name"] for column in target_inspector.get_columns(table_name)}
                common_columns = [column for column in source_columns if column in target_columns]
                if not common_columns:
                    print(f"Skipping table without common columns: {table_name}")
                    continue

                primary_keys = table_primary_keys(target_inspector, table_name)
                source_rows = sqlite_connection.execute(f'SELECT * FROM "{table_name}"').fetchall()
                inserted = 0
                skipped = 0

                for sqlite_row in source_rows:
                    row = {column: sqlite_row[column] for column in common_columns}
                    if row_exists(target_connection, table_name, primary_keys, row):
                        skipped += 1
                        continue

                    insert_row(target_connection, table_name, common_columns, row)
                    inserted += 1

                inserted_total += inserted
                skipped_total += skipped
                print(f"{table_name}: inserted={inserted}, skipped_existing={skipped}")
    finally:
        sqlite_connection.close()

    print(f"Done. Inserted {inserted_total} rows. Skipped existing {skipped_total} rows. No rows were deleted.")


if __name__ == "__main__":
    main()
