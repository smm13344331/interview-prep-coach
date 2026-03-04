"""Configuration utilities for interview prep coach."""

from .paths import (
    get_data_dir,
    get_progress_file,
    get_improvement_file,
    get_questions_file,
    get_bundled_questions_file,
    get_user_questions_file,
    get_agent_prompt_file,
    get_claude_dir,
    get_claude_skills_dir,
    get_claude_mcp_config,
    ensure_editable_material_exists,
)

__all__ = [
    "get_data_dir",
    "get_progress_file",
    "get_improvement_file",
    "get_questions_file",
    "get_bundled_questions_file",
    "get_user_questions_file",
    "get_agent_prompt_file",
    "get_claude_dir",
    "get_claude_skills_dir",
    "get_claude_mcp_config",
    "ensure_editable_material_exists",
]
