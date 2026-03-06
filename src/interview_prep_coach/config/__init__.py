"""Configuration utilities for interview prep coach."""

from .paths import (
    get_data_dir,
    get_database_file,
    get_bundled_questions_file,
    get_agent_prompt_file,
    get_claude_dir,
    get_claude_skills_dir,
    get_claude_mcp_config,
)
from .installer import ClaudeCodeInstaller

__all__ = [
    "get_data_dir",
    "get_database_file",
    "get_bundled_questions_file",
    "get_agent_prompt_file",
    "get_claude_dir",
    "get_claude_skills_dir",
    "get_claude_mcp_config",
    "ClaudeCodeInstaller",
]
