"""Installation logic for Claude Code integration."""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple

from .paths import (
    get_claude_dir,
    get_claude_skills_dir,
    get_claude_mcp_config,
    get_agent_prompt_file,
    ensure_data_files_exist,
)


class ClaudeCodeInstaller:
    """Handles installation/uninstallation of interview prep coach into Claude Code."""

    def __init__(self):
        """Initialize installer."""
        self.claude_dir = get_claude_dir()
        self.skills_dir = get_claude_skills_dir()
        self.settings_file = get_claude_mcp_config()

    def is_installed(self) -> Tuple[bool, Dict[str, bool]]:
        """
        Check if interview prep coach is installed.

        Returns:
            Tuple of (is_fully_installed, details_dict)
        """
        skill_installed = (self.skills_dir / 'prep' / 'SKILL.md').exists()
        mcp_configured = self._is_mcp_configured()

        details = {
            'skill': skill_installed,
            'mcp_server': mcp_configured,
            'claude_dir_exists': self.claude_dir.exists()
        }

        is_fully_installed = all(details.values())

        return is_fully_installed, details

    def _is_mcp_configured(self) -> bool:
        """Check if MCP server is configured in settings.json."""
        if not self.settings_file.exists():
            return False

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

            return 'mcpServers' in settings and 'interview-prep-coach' in settings['mcpServers']
        except (json.JSONDecodeError, IOError):
            return False

    def install(self, force: bool = False) -> Dict[str, Any]:
        """
        Install interview prep coach to Claude Code.

        Args:
            force: Force reinstall even if already installed

        Returns:
            Dictionary with installation results
        """
        results = {
            'success': False,
            'steps': {},
            'errors': []
        }

        # Check if Claude Code directory exists
        if not self.claude_dir.exists():
            results['errors'].append(
                f"Claude Code directory not found: {self.claude_dir}\n"
                "Please ensure Claude Code is installed and has been run at least once."
            )
            return results

        # Check if already installed
        if not force:
            is_installed, details = self.is_installed()
            if is_installed:
                results['errors'].append("Interview prep coach is already installed. Use --force to reinstall.")
                results['steps'] = details
                return results

        # Step 1: Install skill
        try:
            self._install_skill()
            results['steps']['skill'] = True
        except Exception as e:
            results['errors'].append(f"Failed to install skill: {e}")
            results['steps']['skill'] = False

        # Step 2: Configure MCP server
        try:
            self._configure_mcp_server()
            results['steps']['mcp_server'] = True
        except Exception as e:
            results['errors'].append(f"Failed to configure MCP server: {e}")
            results['steps']['mcp_server'] = False

        # Step 3: Initialize data directory
        try:
            ensure_data_files_exist()
            results['steps']['data_files'] = True
        except Exception as e:
            results['errors'].append(f"Failed to initialize data files: {e}")
            results['steps']['data_files'] = False

        # Overall success
        results['success'] = len(results['errors']) == 0

        return results

    def _install_skill(self) -> None:
        """Install /prep skill to Claude Code."""
        skill_dir = self.skills_dir / 'prep'
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / 'SKILL.md'

        # Read agent prompt to embed in skill
        agent_prompt_file = get_agent_prompt_file()
        with open(agent_prompt_file, 'r', encoding='utf-8') as f:
            agent_prompt = f.read()

        # Create skill definition
        skill_content = f"""---
name: prep
description: Interactive technical interview preparation coach with progress tracking and continuous improvement
arguments:
  - name: mode
    description: "Session mode: continue (resume last session), weak (practice weak areas), mock (mock interview), section (practice specific section)"
    required: false
  - name: topic
    description: "Specific topic/section to practice from available material"
    required: false
---

{agent_prompt}

# MCP Tools Available

You have access to **19 MCP tools** from the `interview-prep-coach` server:

## Question Management
- **get-next-question** - Get next question in sequence
- **get-question** - Get specific question by location
- **parse-questions** - Parse all questions in section/subsection
- **search-questions** - Search questions by keyword
- **get-sections** - List all available sections
- **get-subsections** - List subsections for a section

## Progress Tracking
- **get-progress** - Load current learning progress
- **update-progress** - Update progress after each question
- **get-weak-areas** - Get weak areas (<60% accuracy)
- **get-statistics** - Get overall statistics

## Improvement System
- **log-improvement** - Record material quality issues
- **get-improvements** - View pending/implemented improvements

## Material Editing
- **apply-improvement** - Apply logged improvement to material
- **edit-question** - Directly edit question/answer
- **add-question** - Add new question to material
- **refresh-material** - Reload after edits
- **get-material-info** - Check material source/status
- **reset-material** - Revert to original material
- **export-material** - Backup material to file

# Usage

Start with `/prep` or `/prep [mode] [topic]`

Examples:
- `/prep` - Continue from last session
- `/prep weak` - Focus on weak areas
- `/prep mock` - Mock interview mode (random questions)
- `/prep section [name]` - Practice specific section

All tool names must be prefixed with `interview-prep-coach:` when calling them.
"""

        # Write skill file
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(skill_content)

    def _configure_mcp_server(self) -> None:
        """Configure MCP server in settings.json."""
        # Load or create settings
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
        else:
            settings = {}

        # Add MCP server configuration
        if 'mcpServers' not in settings:
            settings['mcpServers'] = {}

        settings['mcpServers']['interview-prep-coach'] = {
            'command': 'interview-prep-coach-server',
            'args': [],
            'description': 'Interview preparation system with progress tracking and continuous improvement'
        }

        # Write settings
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

    def uninstall(self, remove_data: bool = False) -> Dict[str, Any]:
        """
        Uninstall interview prep coach from Claude Code.

        Args:
            remove_data: Whether to remove user data (progress, improvements)

        Returns:
            Dictionary with uninstallation results
        """
        results = {
            'success': False,
            'steps': {},
            'errors': []
        }

        # Remove skill
        try:
            skill_dir = self.skills_dir / 'prep'
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
                results['steps']['skill_removed'] = True
            else:
                results['steps']['skill_removed'] = False
        except Exception as e:
            results['errors'].append(f"Failed to remove skill: {e}")
            results['steps']['skill_removed'] = False

        # Remove MCP server configuration
        try:
            self._remove_mcp_server()
            results['steps']['mcp_server_removed'] = True
        except Exception as e:
            results['errors'].append(f"Failed to remove MCP server: {e}")
            results['steps']['mcp_server_removed'] = False

        # Optionally remove data
        if remove_data:
            try:
                from .paths import get_data_dir
                data_dir = get_data_dir()
                if data_dir.exists():
                    shutil.rmtree(data_dir)
                    results['steps']['data_removed'] = True
                else:
                    results['steps']['data_removed'] = False
            except Exception as e:
                results['errors'].append(f"Failed to remove data: {e}")
                results['steps']['data_removed'] = False
        else:
            results['steps']['data_removed'] = False

        # Overall success
        results['success'] = len(results['errors']) == 0

        return results

    def _remove_mcp_server(self) -> None:
        """Remove MCP server from settings.json."""
        if not self.settings_file.exists():
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

            if 'mcpServers' in settings and 'interview-prep-coach' in settings['mcpServers']:
                del settings['mcpServers']['interview-prep-coach']

                # Write updated settings
                with open(self.settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
        except (json.JSONDecodeError, IOError):
            pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed installation status.

        Returns:
            Dictionary with status information
        """
        is_installed, details = self.is_installed()

        from .paths import get_data_dir, get_progress_file, get_improvement_file

        data_dir = get_data_dir()
        progress_file = get_progress_file()
        improvement_file = get_improvement_file()

        return {
            'installed': is_installed,
            'components': details,
            'data_directory': str(data_dir),
            'data_initialized': progress_file.exists() and improvement_file.exists(),
            'skill_location': str(self.skills_dir / 'prep' / 'SKILL.md'),
            'settings_location': str(self.settings_file)
        }
