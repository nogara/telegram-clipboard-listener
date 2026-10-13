import sqlite3
from typing import Callable


class UrlDatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def __enter__(self):
        self.conn = self.connect_db()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def connect_db(self) -> sqlite3.Connection:
        """Connects to the specified SQLite database."""
        return sqlite3.connect(self.db_name)

    def initialize_database(self):
        """Initializes the database with the given schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE
        )
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(schema)
            self.conn.commit()
            return True

    def check_record_exists(self, url) -> bool:
        """Checks if a record exists that matches the query and parameters."""
        with self.conn:
            cursor = self.conn.execute("SELECT id FROM urls WHERE url = ?", (url,))
            result = cursor.fetchone()
            return result is not None

    def add_record(self, url, check_params: tuple = ()) -> bool:
        """Adds a record to the database, optionally checking if it exists first."""

        if self.check_record_exists(url):
            return False
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO urls (url) VALUES (?)", (url,))
                self.conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
