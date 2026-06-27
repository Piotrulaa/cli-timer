import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DB_FILE_NAME = "timer_db.sqlite3"
DB_PATH = Path(__file__).resolve().parent / DB_FILE_NAME


class DatabaseConnector:
    def __init__(self) -> None:
        self.db_path = DB_PATH

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row

        # Prevent invalid references between related tables.
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def create_example_table(self) -> None:
        with self._connect() as connection:
            connection.execute("""
				CREATE TABLE IF NOT EXISTS timer_entries (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					start_datetime TEXT NOT NULL,
					tracked_minutes INTEGER NOT NULL DEFAULT 0 CHECK(tracked_minutes >= 0),
					description TEXT
				)
				""")

    def add_entry(
        self, start_datetime: datetime, tracked_minutes: int = 0, description: str = ""
    ) -> int:
        if tracked_minutes < 0:
            raise ValueError("tracked_minutes must be >= 0")

        with self._connect() as connection:
            cursor = connection.execute(
                """
				INSERT INTO timer_entries (start_datetime, tracked_minutes, description)
				VALUES (?, ?, ?)
				""",
                (start_datetime.isoformat(), tracked_minutes, description),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to retrieve inserted record id")
            return int(cursor.lastrowid)

    def update_entry(
        self,
        entry_id: int,
        start_datetime: datetime,
        tracked_minutes: int,
        description: str,
    ) -> bool:
        if tracked_minutes < 0:
            raise ValueError("tracked_minutes must be >= 0")

        with self._connect() as connection:
            cursor = connection.execute(
                """
				UPDATE timer_entries
				SET start_datetime = ?,
					tracked_minutes = ?,
					description = ?
				WHERE id = ?
				""",
                (start_datetime.isoformat(), tracked_minutes, description, entry_id),
            )
            return cursor.rowcount > 0

    def delete_entry(self, entry_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
				DELETE FROM timer_entries
				WHERE id = ?
				""",
                (entry_id,),
            )
            return cursor.rowcount > 0

    def get_last_entry(self) -> Optional[sqlite3.Row]:
        with self._connect() as connection:
            cursor = connection.execute("""
				SELECT id, start_datetime, tracked_minutes, description
				FROM timer_entries
				ORDER BY id DESC
				LIMIT 1
				""")
            return cursor.fetchone()

    def get_entries(self, limit: int) -> list[sqlite3.Row]:
        if limit <= 0:
            raise ValueError("limit must be > 0")

        with self._connect() as connection:
            cursor = connection.execute(
                """
				SELECT id, start_datetime, tracked_minutes, description
				FROM timer_entries
				ORDER BY id DESC
				LIMIT ?
				""",
                (limit,),
            )
            return cursor.fetchall()

    def get_entries_by_date(self, entry_date: date) -> list[sqlite3.Row]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
				SELECT id, start_datetime, tracked_minutes, description
				FROM timer_entries
				WHERE date(start_datetime) = ?
				ORDER BY id ASC
				""",
                (entry_date.isoformat(),),
            )
            return cursor.fetchall()
