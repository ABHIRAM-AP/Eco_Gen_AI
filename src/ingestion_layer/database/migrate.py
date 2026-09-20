import sqlite3
import os
import logging

logger = logging.getLogger("ecogen.migrate")

INFERENCE_EVENTS_COLUMNS = [
    ("provider", "VARCHAR"),
    ("pue", "FLOAT DEFAULT 1.2"),
    ("gpu_model", "VARCHAR"),
    ("num_gpus_used", "INTEGER DEFAULT 1"),
    ("batch_size", "INTEGER DEFAULT 1"),
    ("cost_usd", "FLOAT"),
    ("department", "VARCHAR"),
    ("use_case", "VARCHAR"),
    ("param_count_b", "FLOAT"),
    ("active_param_count_b", "FLOAT"),
]

HARDWARE_SNAPSHOTS_COLUMNS = [
    ("idle_power_baseline_w", "FLOAT"),
    ("hardware_install_date", "DATETIME"),
]


def get_existing_columns(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name});")
    rows = cursor.fetchall()
    # row format: (cid, name, type, notnull, dflt_value, pk)
    return {row[1] for row in rows}


def run_migrations(db_path: str = "ecogen.db") -> list[str]:
    """
    Safely adds missing columns to SQLite database tables without altering or dropping existing rows.
    """
    if not os.path.exists(db_path):
        logger.info(f"Database {db_path} does not exist yet; skipping ALTER TABLE.")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    applied_migrations = []

    try:
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inference_events';")
        if cursor.fetchone():
            existing = get_existing_columns(cursor, "inference_events")
            for col_name, col_def in INFERENCE_EVENTS_COLUMNS:
                if col_name not in existing:
                    query = f"ALTER TABLE inference_events ADD COLUMN {col_name} {col_def};"
                    cursor.execute(query)
                    applied_migrations.append(f"inference_events.{col_name}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hardware_snapshots';")
        if cursor.fetchone():
            existing = get_existing_columns(cursor, "hardware_snapshots")
            for col_name, col_def in HARDWARE_SNAPSHOTS_COLUMNS:
                if col_name not in existing:
                    query = f"ALTER TABLE hardware_snapshots ADD COLUMN {col_name} {col_def};"
                    cursor.execute(query)
                    applied_migrations.append(f"hardware_snapshots.{col_name}")

        conn.commit()
    finally:
        conn.close()

    return applied_migrations


if __name__ == "__main__":
    added = run_migrations()
    print(f"Applied migrations: {added}")
