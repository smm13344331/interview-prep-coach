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


def get_progress_file() -> Path:
    """
    Get path to learning progress JSON file.

    Returns:
        Path to learning-progress.json in data directory
    """
    return get_data_dir() / 'learning-progress.json'


def get_improvement_file() -> Path:
    """
    Get path to improvement log JSON file.

    Returns:
        Path to improvement-log.json in data directory
    """
    return get_data_dir() / 'improvement-log.json'


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


def get_user_questions_file() -> Path:
    """
    Get user-editable questions file in data directory.

    This is a copy of the bundled file that can be modified.
    Changes to this file are preserved across package updates.

    Returns:
        Path to user's editable questions file
    """
    return get_data_dir() / 'interview-prep-material.md'


def get_questions_file() -> Path:
    """
    Get questions file, preferring user copy over bundled version.

    Uses copy-on-write pattern:
    - If user has edited copy, use that
    - Otherwise, use bundled version

    Returns:
        Path to questions file to use
    """
    user_file = get_user_questions_file()
    if user_file.exists():
        return user_file
    return get_bundled_questions_file()


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


def get_progress_template() -> Path:
    """
    Get bundled progress template file from package data.

    Returns:
        Path to learning-progress-template.json
    """
    try:
        from importlib.resources import files
        resource = files('interview_prep_coach.data') / 'learning-progress-template.json'
        return Path(str(resource))
    except (ImportError, AttributeError):
        from importlib.resources import path as resource_path
        with resource_path('interview_prep_coach.data', 'learning-progress-template.json') as p:
            return Path(p)


def get_improvement_template() -> Path:
    """
    Get bundled improvement log template file from package data.

    Returns:
        Path to improvement-log-template.json
    """
    try:
        from importlib.resources import files
        resource = files('interview_prep_coach.data') / 'improvement-log-template.json'
        return Path(str(resource))
    except (ImportError, AttributeError):
        from importlib.resources import path as resource_path
        with resource_path('interview_prep_coach.data', 'improvement-log-template.json') as p:
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


def ensure_data_files_exist() -> None:
    """
    Ensure data files exist, copying from templates if needed.

    This should be called on first run or after installation.
    Does NOT copy questions file - that's done only when needed for editing.
    """
    import shutil
    import json

    progress_file = get_progress_file()
    improvement_file = get_improvement_file()

    # Copy progress template if file doesn't exist
    if not progress_file.exists():
        template = get_progress_template()
        # Read and write to handle both resource types
        with open(template, 'r') as src:
            with open(progress_file, 'w') as dst:
                dst.write(src.read())

    # Copy improvement template if file doesn't exist
    if not improvement_file.exists():
        template = get_improvement_template()
        with open(template, 'r') as src:
            with open(improvement_file, 'w') as dst:
                dst.write(src.read())


def ensure_editable_material_exists() -> Path:
    """
    Ensure user has an editable copy of the questions material.

    Copy-on-write: Creates user copy from bundled version on first edit.

    Returns:
        Path to user's editable material file
    """
    user_file = get_user_questions_file()

    if not user_file.exists():
        bundled_file = get_bundled_questions_file()
        # Copy bundled to user directory
        with open(bundled_file, 'r', encoding='utf-8') as src:
            with open(user_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

    return user_file
