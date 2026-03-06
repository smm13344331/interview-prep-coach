"""Installation logic for Claude Code integration."""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from .paths import (
    get_claude_dir,
    get_claude_skills_dir,
    get_claude_mcp_config,
    get_agent_prompt_file,
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
        """
        Check if MCP server is configured.

        Directly reads .claude.json to avoid hanging claude mcp commands.
        """
        try:
            config = self._read_claude_config()
            if not config:
                return False

            # Get current project path
            cwd = os.getcwd()

            # Check if project config exists (use 'projects' key, not 'projectConfigs')
            project_config = config.get('projects', {}).get(cwd)
            if not project_config:
                return False

            # Check if our MCP server is configured
            mcp_servers = project_config.get('mcpServers', {})
            return 'interview-prep-coach' in mcp_servers

        except Exception:
            return False

    def _read_claude_config(self) -> Optional[Dict[str, Any]]:
        """Read .claude.json configuration file."""
        # .claude.json is in the home directory, not in .claude/
        claude_json = Path.home() / '.claude.json'
        if not claude_json.exists():
            return None

        try:
            with open(claude_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _write_claude_config(self, config: Dict[str, Any]) -> None:
        """Write .claude.json configuration file."""
        # .claude.json is in the home directory, not in .claude/
        claude_json = Path.home() / '.claude.json'

        # Write with pretty formatting to match Claude's style
        with open(claude_json, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            f.write('\n')  # Add trailing newline

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

        # Step 3: Database initialization (handled in cli.py)
        results['steps']['data_files'] = True

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

---

## MCP Tools Discovery

You have access to MCP tools from the `interview-prep-coach` server. Claude Code automatically discovers these tools on-demand through semantic search.

**Tool Categories Available:**
- **Session Management**: Starting and ending practice sessions
- **Question Retrieval**: Getting questions by section, subsection, or search
- **Progress Tracking**: Recording answers and viewing statistics
- **Weak Area Analysis**: Identifying topics that need more practice
- **Material Editing**: Adding, editing, or deleting questions
- **Improvement Logging**: Recording and tracking material quality issues
- **Material Management**: Importing, cloning, activating different question sets

**How to Use Tools:**
Use Claude Code's natural tool discovery - simply describe what you need to do (e.g., "start a session", "get next question", "track this answer") and the appropriate tools will be found automatically through semantic search. The MCP server provides detailed descriptions for each tool.

**Key Workflow Patterns:**
1. **Session Start**: `start-session` → `get-statistics` → present options
2. **Question Flow**: `get-next-question` → user answers → `update-progress` → feedback
3. **Weak Areas**: `get-weak-areas` → `get-all-questions` → targeted practice
4. **Material Quality**: notice issue → `log-improvement` → `edit-question` → `mark-improvement-implemented`

---

## Usage Examples

Start with `/prep` or `/prep [mode] [topic]`

**Session Modes:**
- `/prep` - Continue from last session (recommended)
- `/prep weak` - Focus on weak areas (<60% accuracy)
- `/prep mock` - Mock interview mode (random questions)
- `/prep section [name]` - Practice specific section

**During Session:**
- Answer questions naturally
- Type "hint" for a hint
- Type "skip" to skip
- Type "explain" to see the answer
"""

        # Write skill file
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(skill_content)

    def _configure_mcp_server(self) -> None:
        """
        Configure MCP server by directly modifying .claude.json.

        This avoids the hanging claude mcp commands and provides direct control.
        """
        # Read current config
        config = self._read_claude_config()
        if config is None:
            raise RuntimeError(f"Could not read Claude config file: {Path.home() / '.claude.json'}")

        # Get current project path
        cwd = os.getcwd()

        # Ensure projects exists (use 'projects' key, not 'projectConfigs')
        if 'projects' not in config:
            config['projects'] = {}

        # Ensure current project exists in config
        if cwd not in config['projects']:
            config['projects'][cwd] = {
                'allowedTools': [],
                'mcpContextUris': [],
                'mcpServers': {},
                'enabledMcpjsonServers': [],
                'disabledMcpjsonServers': [],
                'hasTrustDialogAccepted': False,
            }

        # Get project config
        project_config = config['projects'][cwd]

        # Ensure mcpServers exists
        if 'mcpServers' not in project_config:
            project_config['mcpServers'] = {}

        # Add our MCP server configuration
        project_config['mcpServers']['interview-prep-coach'] = {
            'type': 'stdio',
            'command': 'interview-prep-coach-server',
            'args': [],
            'env': {}
        }

        # Write back to file
        self._write_claude_config(config)

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
        """
        Remove MCP server by directly modifying .claude.json.

        This avoids the hanging claude mcp commands.
        """
        try:
            # Read current config
            config = self._read_claude_config()
            if config is None:
                return  # Nothing to remove

            # Get current project path
            cwd = os.getcwd()

            # Check if project config exists (use 'projects' key, not 'projectConfigs')
            if 'projects' not in config or cwd not in config['projects']:
                return  # Nothing to remove

            project_config = config['projects'][cwd]

            # Remove our MCP server if it exists
            if 'mcpServers' in project_config:
                project_config['mcpServers'].pop('interview-prep-coach', None)

            # Write back to file
            self._write_claude_config(config)

        except Exception:
            # Silently ignore errors - server might not exist
            pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed installation status.

        Returns:
            Dictionary with status information
        """
        is_installed, details = self.is_installed()

        from .paths import get_data_dir, get_database_file

        data_dir = get_data_dir()
        db_file = get_database_file()

        return {
            'installed': is_installed,
            'components': details,
            'data_directory': str(data_dir),
            'data_initialized': db_file.exists(),
            'database_location': str(db_file),
            'skill_location': str(self.skills_dir / 'prep' / 'SKILL.md'),
            'settings_location': str(self.settings_file)
        }
