"""
SQLite compatibility shim for CVE-2022-35737 mitigation.

This module ensures we use pysqlite3-binary (bundled SQLite 3.42+) instead of
the system sqlite3 which may be vulnerable to CVE-2022-35737.

The CVE affects FTS5 content tables with UPDATE triggers, causing database
corruption ("database disk image is malformed" errors).

pysqlite3-binary provides:
- Pre-compiled wheel with bundled SQLite
- Cross-platform (Linux, macOS, Windows)
- Drop-in replacement for sqlite3

This shim is imported FIRST by all modules that need database access.
"""

import sys
import logging

logger = logging.getLogger(__name__)

# Try to use pysqlite3-binary first (bundled recent SQLite)
try:
    import pysqlite3 as sqlite3

    logger.debug(
        f"Using pysqlite3 with bundled SQLite {sqlite3.sqlite_version} "
        f"(libsqlite {sqlite3.version})"
    )

    # Verify we have a safe version (3.38.0+)
    version_tuple = tuple(map(int, sqlite3.sqlite_version.split('.')))
    if version_tuple < (3, 38, 0):
        logger.warning(
            f"pysqlite3 has SQLite {sqlite3.sqlite_version} but 3.38.0+ is recommended. "
            f"CVE-2022-35737 may still affect this version."
        )
    else:
        logger.info(
            f"✓ Using safe SQLite {sqlite3.sqlite_version} via pysqlite3-binary "
            f"(CVE-2022-35737 mitigated)"
        )

except ImportError:
    # Fallback to system sqlite3 with version check
    import sqlite3

    version_tuple = tuple(map(int, sqlite3.sqlite_version.split('.')))

    if version_tuple < (3, 38, 0):
        logger.error(
            f"CRITICAL: System SQLite {sqlite3.sqlite_version} has CVE-2022-35737. "
            f"Install pysqlite3-binary: pip install pysqlite3-binary"
        )
        print(
            f"\n{'='*70}\n"
            f"ERROR: SQLite version too old (CVE-2022-35737)\n"
            f"{'='*70}\n"
            f"Your system SQLite: {sqlite3.sqlite_version}\n"
            f"Required: 3.38.0 or higher\n\n"
            f"This vulnerability causes database corruption in FTS5 operations.\n\n"
            f"Solution:\n"
            f"  pip install --upgrade pysqlite3-binary\n\n"
            f"Or reinstall interview-prep-coach:\n"
            f"  pip install --force-reinstall interview-prep-coach\n"
            f"{'='*70}\n",
            file=sys.stderr
        )
        sys.exit(1)
    else:
        logger.info(
            f"Using system SQLite {sqlite3.sqlite_version} (safe version)"
        )

# Export for use by other modules
__all__ = ['sqlite3']
