"""Database management for interview prep coach."""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

# Use compatibility shim to ensure safe SQLite version (CVE-2022-35737)
from .._sqlite_compat import sqlite3

from ..config.paths import get_database_file
from .schema import get_schema_sql, CURRENT_SCHEMA_VERSION

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and operations.

    Provides a simple interface for database operations with proper
    connection management, transactions, and error handling.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        self.db_path = db_path or get_database_file()
        self._connection: Optional[sqlite3.Connection] = None
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection, creating if needed.

        Returns:
            SQLite connection object with row factory set
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode for better control
            )
            # Return rows as dictionaries
            self._connection.row_factory = sqlite3.Row
            # Enable foreign key constraints
            self._connection.execute("PRAGMA foreign_keys = ON")
            logger.debug("Database connection established")

        return self._connection

    def close(self):
        """Close database connection if open."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Database connection closed")

    def initialize_schema(self) -> None:
        """
        Initialize database schema from SQL file.

        Creates all tables if they don't exist. Safe to call multiple times.
        """
        conn = self.get_connection()
        schema_sql = get_schema_sql()

        try:
            conn.executescript(schema_sql)
            logger.info(f"Database schema initialized at version {CURRENT_SCHEMA_VERSION}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize schema: {e}", exc_info=True)
            raise

    def get_schema_version(self) -> int:
        """
        Get current schema version from database.

        Returns:
            Schema version number, or 0 if not initialized
        """
        try:
            result = self.fetchone(
                "SELECT MAX(version) as version FROM schema_version"
            )
            return result['version'] if result and result['version'] else 0
        except sqlite3.Error:
            return 0

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            Cursor object

        Raises:
            sqlite3.Error: If query execution fails
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            # Only commit if not in transaction mode (isolation_level is None in autocommit)
            if conn.isolation_level is None:
                conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            raise

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            Dictionary of column names to values, or None if no results
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            raise

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            List of dictionaries, one per row
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            raise

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db.transaction():
                db.execute("INSERT ...")
                db.execute("UPDATE ...")
            # Automatically commits on success, rolls back on exception
        """
        conn = self.get_connection()
        # Disable autocommit temporarily
        conn.isolation_level = 'DEFERRED'
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}", exc_info=True)
            raise
        finally:
            # Re-enable autocommit
            conn.isolation_level = None

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists, False otherwise
        """
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def count_records(self, table_name: str, where_clause: str = "", params: tuple = ()) -> int:
        """
        Count records in a table.

        Args:
            table_name: Name of the table
            where_clause: Optional WHERE clause (without WHERE keyword)
            params: Parameters for WHERE clause

        Returns:
            Number of records
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        result = self.fetchone(query, params)
        return result['count'] if result else 0

    def backup(self, backup_path: Path) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path where backup should be saved

        Returns:
            True if backup successful, False otherwise
        """
        try:
            conn = self.get_connection()
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            logger.info(f"Database backed up to {backup_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
