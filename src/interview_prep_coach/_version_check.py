"""Runtime version checks for Python.

SQLite version checking is now handled by _sqlite_compat module.
"""

import sys


def check_python_version(min_version=(3, 10, 0)):
    """
    Check if Python version meets minimum requirements.

    Args:
        min_version: Tuple of (major, minor, micro) version

    Raises:
        SystemExit: If Python version is too old
    """
    if sys.version_info < min_version:
        current = ".".join(map(str, sys.version_info[:3]))
        required = ".".join(map(str, min_version))
        print(f"ERROR: Python {required} or higher is required", file=sys.stderr)
        print(f"You are running Python {current}", file=sys.stderr)
        print("\nInterview Prep Coach requires Python 3.10+", file=sys.stderr)
        print("Please upgrade Python and try again.", file=sys.stderr)
        sys.exit(1)


def check_versions():
    """
    Check Python version.

    SQLite version checking is handled automatically by _sqlite_compat module
    which uses pysqlite3-binary to ensure a safe version.

    Raises:
        SystemExit: If Python version doesn't meet requirements
    """
    check_python_version()
