"""Path resolution for interview prep coach data and configuration files."""

import os
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """
    Get user data directory (XDG-compliant).

    Returns directory where progress and improvement logs are stored.
    Creates directory if it doesn't exist.

    Returns:
        Path to data directory (~/.local/share/interview-prep-coach or XDG_DATA_HOME)
    """
    if xdg_data := os.environ.get('XDG_DATA_HOME'):
        base = Path(xdg_data)
    else:
        base = Path.home() / '.local' / 'share'

    data_dir = base / 'interview-prep-coach'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_file() -> Path:
    """
    Get path to SQLite database file.

    Returns:
        Path to interview-prep.db in data directory
    """
    return get_data_dir() / 'interview-prep.db'


def get_bundled_questions_file() -> Path:
    """
    Get bundled questions file from package data (read-only).

    Returns:
        Path to bundled interview questions markdown file
    """
    try:
        # Python 3.9+
        from importlib.resources import files
        resource = files('interview_prep_coach.data') / 'interview-prep-java-spring-infra.md'
        # Return as Path for compatibility
        return Path(str(resource))
    except (ImportError, AttributeError):
        # Python 3.8 fallback
        from importlib.resources import path as resource_path
        with resource_path('interview_prep_coach.data', 'interview-prep-java-spring-infra.md') as p:
            return Path(p)


def get_agent_prompt_file() -> Path:
    """
    Get bundled agent prompt file from package data.

    Returns:
        Path to agent prompt markdown file
    """
    try:
        # Python 3.9+
        from importlib.resources import files
        resource = files('interview_prep_coach.data') / 'interview-coach-agent-prompt.md'
        return Path(str(resource))
    except (ImportError, AttributeError):
        # Python 3.8 fallback
        from importlib.resources import path as resource_path
        with resource_path('interview_prep_coach.data', 'interview-coach-agent-prompt.md') as p:
            return Path(p)


def get_claude_dir() -> Path:
    """
    Get Claude Code configuration directory.

    Returns:
        Path to ~/.claude directory
    """
    return Path.home() / '.claude'


def get_claude_skills_dir() -> Path:
    """
    Get Claude Code skills directory.

    Returns:
        Path to ~/.claude/skills directory
    """
    skills_dir = get_claude_dir() / 'skills'
    skills_dir.mkdir(parents=True, exist_ok=True)
    return skills_dir


def get_claude_mcp_config() -> Path:
    """
    Get Claude Code settings.json file for MCP server configuration.

    Returns:
        Path to ~/.claude/settings.json
    """
    return get_claude_dir() / 'settings.json'
