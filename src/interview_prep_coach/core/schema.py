"""Database schema definitions and version management."""

from pathlib import Path
from typing import List

# Current schema version
CURRENT_SCHEMA_VERSION = 1

# Table names
TABLES = [
    'schema_version',
    'materials',
    'questions',
    'questions_fts',
    'sessions',
    'progress',
    'improvements',
    'plugins',
    'user_preferences'
]


def get_schema_sql() -> str:
    """
    Get the SQL schema definition.

    Returns:
        SQL string containing all CREATE TABLE statements
    """
    try:
        # Python 3.9+
        from importlib.resources import files
        resource = files('interview_prep_coach.data') / 'schema.sql'
        return resource.read_text(encoding='utf-8')
    except (ImportError, AttributeError):
        # Python 3.8 fallback
        from importlib.resources import read_text
        return read_text('interview_prep_coach.data', 'schema.sql', encoding='utf-8')


def validate_schema_version(version: int) -> bool:
    """
    Validate that a schema version is within acceptable range.

    Args:
        version: Schema version number

    Returns:
        True if version is valid, False otherwise
    """
    return 1 <= version <= CURRENT_SCHEMA_VERSION


def get_table_list() -> List[str]:
    """
    Get list of all tables in the schema.

    Returns:
        List of table names
    """
    return TABLES.copy()
