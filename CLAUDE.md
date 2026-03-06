# Interview Prep Coach - Development Guide

## Project Overview

This is an AI-powered technical interview preparation system packaged as a distributable Python application. It integrates with Claude Code as a native `/prep` skill and provides 19 MCP tools for interactive learning.

**Key Philosophy:**
- Technology-agnostic (works for any technical interview material)
- MCP-native (all operations via MCP tools, no hardcoded paths)
- Self-improving (AI can enhance its own teaching materials)
- User-friendly (single command installation)

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│ User Interface                                               │
│ - /prep skill in Claude Code                                 │
│ - CLI commands (interview-prep-coach)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ MCP Server (interview-prep-coach-server)                     │
│ - 19 tools organized in 4 categories                         │
│ - Stateless, database-backed via DatabaseManager            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Core Modules                                                 │
│ - DatabaseManager: SQLite with schema management            │
│ - PluginManager: material source plugin lifecycle           │
│ - ProgressTracker: learning state tracking                  │
│ - ImprovementLogger: quality tracking                       │
│ - QuestionParser: question retrieval from database          │
│ - MaterialEditor: material CRUD operations                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Plugin System                                                │
│ - MaterialPlugin base class: plugin interface               │
│ - PluginManager: install, enable, disable, load             │
│ - MarkdownImporter: parse markdown to database              │
│ - Bundled plugins: JavaSpringPlugin                         │
│ - Extensible: custom plugins for APIs, scrapers, etc.       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Data Layer                                                   │
│ - SQLite database: interview_prep.db                        │
│   * materials: material sources (plugins, bundled, user)    │
│   * questions: all interview questions with FTS5 search     │
│   * progress: per-question attempt tracking                 │
│   * improvements: material quality issues                   │
│   * sessions: learning session history                      │
│   * plugins: plugin registry                                │
│ - XDG-compliant: ~/.local/share/interview-prep-coach/       │
│ - Schema versioning with migrations                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

**1. Plugin-Based Material System**
```python
# Define a material plugin
class MyPlugin(MaterialPlugin):
    @property
    def plugin_id(self) -> str:
        return "my-plugin"

    def import_material(self, db: DatabaseManager, material_id: str) -> bool:
        # Import questions into database
        pass

# Users can switch between material sources
db.execute("UPDATE materials SET is_active = TRUE WHERE id = ?", (material_id,))
```

**Why:** Flexible material sources (bundled, files, APIs), easy to extend, survives package updates.

**2. MCP-Native Operations**
```python
# WRONG: Direct file access
with open('/path/to/progress.json') as f:
    data = json.load(f)

# RIGHT: Via MCP tool
progress = await call_tool("interview-prep-coach:get-progress")
```

**Why:** Consistent interface, tool permissions, can be used by other agents.

**3. Stateless MCP Server**
```python
# Each tool call is independent
# State is persisted via Core modules to disk
# Server just coordinates between tools and core logic
```

**Why:** Simple, testable, follows MCP patterns.

**3. Database-First Architecture**
```python
# All state in SQLite database
db = DatabaseManager()
db.initialize_schema()

# Questions, progress, improvements all in database
questions = db.fetchall("SELECT * FROM questions WHERE material_id = ?", (id,))
```

**Why:** Single source of truth, atomic transactions, powerful queries, FTS search.

**4. SQLite Compatibility Shim (CVE-2022-35737 Mitigation)**
```python
# All modules use _sqlite_compat instead of direct sqlite3 import
from .._sqlite_compat import sqlite3

# This automatically uses pysqlite3-binary if available
# Falls back to system sqlite3 with version check
```

**Why:** System SQLite 3.37.x has CVE-2022-35737 causing FTS5 corruption. Using `pysqlite3-binary` bundles SQLite 3.42+ in a wheel package, eliminating the vulnerability.

**Technical Details:**
- `pysqlite3-binary` is a pre-compiled wheel with bundled libsqlite3
- Works across all platforms (Linux, macOS, Windows)
- Drop-in replacement for `sqlite3` module
- No compilation or system dependencies needed
- Automatically used by importing from `_sqlite_compat`

## Code Structure

```
src/interview_prep_coach/
├── cli.py                      # Entry point: interview-prep-coach command
├── server.py                   # Entry point: interview-prep-coach-server (MCP)
├── _sqlite_compat.py           # SQLite compatibility shim (CVE mitigation)
├── _version_check.py           # Python version checks
│
├── config/
│   ├── paths.py               # ALL path logic here (XDG-compliant)
│   └── installer.py           # Claude Code integration (skill + MCP)
│
├── core/                      # Business logic
│   ├── database.py            # DatabaseManager: SQLite operations
│   ├── schema.py              # Schema definitions and versioning
│   ├── plugin_manager.py      # PluginManager: plugin lifecycle
│   ├── progress.py            # ProgressTracker: learning state tracking
│   ├── improvements.py        # ImprovementLogger: quality tracking
│   ├── questions.py           # QuestionParser: question retrieval
│   └── material_editor.py     # MaterialEditor: material management
│
├── plugins/                   # Plugin system
│   ├── base.py                # MaterialPlugin base class
│   ├── importers.py           # MarkdownImporter utility
│   └── bundled/
│       ├── __init__.py
│       └── java_spring_importer.py  # JavaSpringPlugin
│
└── data/                      # Bundled with package (read-only)
    ├── interview-coach-agent-prompt.md      # Agent instructions
    ├── interview-prep-java-spring-infra.md  # Default questions
    └── schema.sql                           # Database schema SQL
```

### Module Responsibilities

**cli.py**
- Commands: install, uninstall, status, reset, info
- Uses: ClaudeCodeInstaller, ProgressTracker
- No business logic, just UI and coordination

**server.py**
- Defines 19 MCP tools
- Instantiates Core modules
- Thin wrapper: validates input → calls Core → formats output
- No business logic

**_sqlite_compat.py**
- SQLite compatibility shim for CVE-2022-35737
- Automatically uses pysqlite3 (bundled SQLite 3.42+) if available
- Falls back to system sqlite3 with version check
- Exports `sqlite3` for use by all modules
- Imported first by all modules needing database access

**_version_check.py**
- Python version checks (3.10+ required)
- Called at entry points (cli.py, server.py)
- SQLite checking delegated to _sqlite_compat

**config/paths.py**
- Single source of truth for ALL file paths
- XDG-compliant: `~/.local/share/interview-prep-coach/`
- Copy-on-write logic
- Functions: `get_*_file()`, `ensure_*_exists()`

**config/installer.py**
- ClaudeCodeInstaller class
- Generates SKILL.md dynamically
- Updates settings.json
- Idempotent operations

**core/*.py**
- Pure business logic
- No file path knowledge (uses paths.py)
- Testable in isolation
- Returns data structures, not strings

**data/**
- Bundled resources
- Accessed via `importlib.resources`
- Never modified (read-only)

## Development Workflow

### Setup

```bash
# Clone and setup
git clone <repo>
cd interview-prep-coach

# Development install
pip install -e .

# Install to Claude Code for testing
interview-prep-coach install --force
```

### Making Changes

**Adding a new MCP tool:**

1. Add tool definition in `server.py` → `list_tools()`
2. Add tool handler in `server.py` → `call_tool()`
3. Add core logic in appropriate `core/*.py` module
4. Update agent prompt in `data/interview-coach-agent-prompt.md`
5. Update README.md if user-facing

**Adding a new core module:**

1. Create `core/new_module.py`
2. Add to `core/__init__.py` exports
3. Use in `server.py`
4. Add tests

**Modifying agent behavior:**

1. Edit `data/interview-coach-agent-prompt.md` (this is the system prompt)
2. Rebuild: `python -m build`
3. Reinstall: `pip install --force-reinstall dist/*.whl`
4. Reinstall to Claude: `interview-prep-coach install --force`
5. Restart Claude Code

### Testing

**Manual testing:**
```bash
# Test CLI
interview-prep-coach status

# Test package import
python -c "from interview_prep_coach.core import ProgressTracker; print('OK')"

# Test MCP server (check it starts)
interview-prep-coach-server --help

# Test in Claude Code
claude
> /prep
```

**Unit testing:**
```python
# Create tests/test_progress.py
from interview_prep_coach.core import ProgressTracker

def test_progress_tracking():
    tracker = ProgressTracker()
    progress = tracker.load_progress()
    assert 'sections' in progress
```

**Integration testing:**
```bash
# Use test_improvements.py as template
python test_improvements.py
```

### Building and Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Check
ls dist/
# Should see: interview_prep_coach-1.0.0-py3-none-any.whl
#             interview_prep_coach-1.0.0.tar.gz

# Install locally
pip install dist/*.whl

# Upload to PyPI (when ready)
twine upload dist/*
```

## Important Patterns

### Path Management

**ALWAYS use paths.py functions:**
```python
from interview_prep_coach.config.paths import get_progress_file

# RIGHT
progress_file = get_progress_file()

# WRONG
progress_file = Path.home() / '.local/share/interview-prep-coach/learning-progress.json'
```

### Database Access

**Always use DatabaseManager:**
```python
from interview_prep_coach.core import DatabaseManager

db = DatabaseManager()
# All data access through database
questions = db.fetchall("SELECT * FROM questions WHERE material_id = ?", (id,))
```

### Plugin Pattern

**For bundled files:**
```python
from interview_prep_coach.config.paths import get_bundled_questions_file
from interview_prep_coach.plugins.importers import MarkdownImporter

# Import into database
bundled_file = get_bundled_questions_file()
importer = MarkdownImporter()
count = importer.import_to_db(db, material_id, bundled_file)
```

### MCP Tool Pattern

```python
@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    try:
        if name == "new-tool":
            # 1. Extract arguments
            param = arguments["param"]

            # 2. Call core module
            result = core_module.do_something(param)

            # 3. Format response
            return [TextContent(type="text", text=json.dumps(result))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

## Extending the System

### Adding New Question Material

**Option 1: Create a new plugin**
```python
# src/interview_prep_coach/plugins/bundled/my_plugin.py
class MyTopicPlugin(MaterialPlugin):
    @property
    def plugin_id(self) -> str:
        return "my-topic"

    def import_material(self, db: DatabaseManager, material_id: str) -> bool:
        # Load your questions from file, API, etc.
        importer = MarkdownImporter()
        return importer.import_to_db(db, material_id, my_file_path)
```

**Option 2: Import via CLI**
```bash
interview-prep-coach materials import my-questions.md --id my-topic --name "My Topic"
interview-prep-coach materials activate my-topic
```

**Option 3: Edit bundled material**
1. Edit `src/interview_prep_coach/data/interview-prep-java-spring-infra.md`
2. Rebuild and reinstall package

### Adding New Learning Modes

1. Update agent prompt with new mode behavior
2. Add mode detection in prompt
3. Update skill arguments in `installer.py`
4. No code changes needed!

### Adding New Improvement Types

1. Update database schema in `data/schema.sql` if needed (add to CHECK constraint)

2. Update agent prompt in `data/interview-coach-agent-prompt.md`:
```markdown
| `new_type` | When to use this type |
```

3. Improvements are stored in database and applied via MaterialEditor

### Adding Analytics

Good places to add:
- `core/progress.py` → add methods to query database
- Add new MCP tool: `get-analytics` in `server.py`
- Query from `progress` and `sessions` tables
- Display in CLI: `interview-prep-coach status`

## Common Tasks

### Change Agent Behavior

**File:** `src/interview_prep_coach/data/interview-coach-agent-prompt.md`

This file becomes the system prompt. Edit it to change:
- How coach interacts
- When to log improvements
- Evaluation criteria
- Session flow

**After editing:** Rebuild and reinstall.

### Change Default Material

**File:** `src/interview_prep_coach/data/interview-prep-java-spring-infra.md`

This is the bundled question bank (imported via JavaSpringPlugin). Edit to:
- Add more questions
- Update for new technologies
- Fix errors
- Change focus areas

**After editing:** Rebuild and reinstall. The plugin will re-import on fresh installs.

### Add CLI Command

**File:** `src/interview_prep_coach/cli.py`

```python
@cli.command()
def new_command():
    """Description of new command."""
    click.echo("Doing something...")
    # Implementation
```

**After editing:** `pip install -e .` then test with `interview-prep-coach new-command`

### Change Skill Name

Currently `/prep`. To change:

1. Edit `installer.py` → `_install_skill()` → change `name: prep`
2. Change directory name: `skills_dir / 'new-name'`
3. Update documentation

## Gotchas and Known Issues

### 1. Skill Loading
**Issue:** Skills only load on Claude Code startup
**Solution:** Always restart Claude Code after `interview-prep-coach install`

### 2. File Structure
**Issue:** Skills MUST be `~/.claude/skills/<name>/SKILL.md` (not loose .md files)
**Solution:** Installer creates proper directory structure

### 3. Tool Name Prefix
**Issue:** MCP tools must be called with prefix: `interview-prep-coach:tool-name`
**Solution:** Agent prompt includes this in examples

### 4. Resource Access
**Issue:** `importlib.resources` API changed in Python 3.9+
**Solution:** `paths.py` handles both old and new API

### 5. Database Schema Changes
**Issue:** If schema changes after release, existing databases break
**Solution:** Add migration script or bump schema version and handle in DatabaseManager

### 6. Claude MCP Commands Hanging
**Issue:** `claude mcp add/remove/get/list` commands hang indefinitely when called via subprocess
**Solution:** Installer directly manipulates `~/.claude.json` instead of calling CLI commands
**Details:**
- The `.claude.json` file is in the home directory (`~/.claude.json`, not `~/.claude/.claude.json`)
- Project configurations are under the `projects` key (not `projectConfigs`)
- Structure: `config['projects'][project_path]['mcpServers']['interview-prep-coach']`
- See `installer.py` methods: `_read_claude_config()`, `_write_claude_config()`, `_configure_mcp_server()`, `_remove_mcp_server()`

## File Locations Reference

### Development
```
interview-prep-coach/              # Git repo
├── src/interview_prep_coach/     # Source code
├── tests/                         # Tests (if added)
├── dist/                          # Built packages (gitignored)
└── build/                         # Build artifacts (gitignored)
```

### After pip install
```
/usr/local/lib/python3.10/dist-packages/interview_prep_coach/
├── cli.py, server.py, etc.       # Installed code
└── data/                          # Bundled resources (read-only)
```

### After interview-prep-coach install
```
~/.claude/
├── skills/prep/SKILL.md          # The /prep command
└── settings.json                 # MCP server config

~/.local/share/interview-prep-coach/
└── interview-prep.db             # SQLite database (all data)
```

## Debugging Tips

### Check installation
```bash
interview-prep-coach status
pip show interview-prep-coach
which interview-prep-coach-server
```

### Check Claude Code integration
```bash
ls -la ~/.claude/skills/prep/SKILL.md
cat ~/.claude/settings.json | grep interview-prep-coach
```

### Check MCP server
```bash
# Enable debug mode in Claude Code
claude --debug

# Look for MCP errors in logs
tail -f ~/.claude/debug/latest
```

### Test core modules directly
```python
from interview_prep_coach.core import DatabaseManager, ProgressTracker

db = DatabaseManager()
tracker = ProgressTracker(db)
stats = tracker.get_statistics('java-spring-bundled')
print(stats)
```

### Test database
```python
from interview_prep_coach.core import DatabaseManager

db = DatabaseManager()
materials = db.fetchall("SELECT * FROM materials")
print(materials)
```

## Version Management

### Bumping Version

1. Update `src/interview_prep_coach/__version__.py`
2. Update `pyproject.toml` → `version = "1.1.0"`
3. Rebuild and test
4. Commit: `git commit -m "Bump version to 1.1.0"`
5. Tag: `git tag v1.1.0`
6. Build: `python -m build`
7. Distribute

### Breaking Changes

If changing:
- Database schema → Add migration or bump major version
- MCP tool signatures → Update agent prompt + bump minor version
- Plugin interface → Add backward compat or bump major version

## Security Considerations

- User data stored locally (no network calls)
- Material edits are local only
- No secrets or credentials stored
- Claude Code handles authentication
- MCP server runs locally only

## Performance Notes

- Database queries: ~1-5ms (indexed)
- Question search (FTS5): ~10-20ms
- Progress tracking: ~5ms (INSERT)
- Material import: ~100-500ms (bulk INSERT with transaction)

## Future Enhancements Ideas

- [ ] Export progress as PDF report
- [ ] Spaced repetition scheduling algorithm
- [ ] Multi-user support with database sync
- [ ] Web dashboard for progress visualization
- [ ] More bundled plugins (Python, System Design, etc.)
- [ ] API-based plugins (fetch questions from LeetCode, HackerRank)
- [ ] Integration with Anki/flashcard apps
- [ ] Voice mode for practice
- [ ] Company-specific question bank plugins
- [ ] Schema migrations for version upgrades

## Getting Help

- **README.md**: User documentation
- **This file (CLAUDE.md)**: Development guide
- **Code comments**: Implementation details
- **Git history**: Why decisions were made

## Summary for Future Claude Sessions

When working on this project:
1. **Read CLAUDE.md first** (you're here!)
2. **Use paths.py** for all file operations
3. **MCP tools** are the public interface
4. **Core modules** contain business logic
5. **Agent prompt** controls behavior
6. **Rebuild + reinstall** after changes
7. **Test with /prep** in Claude Code
8. **Keep README.md** updated for users

This project is designed to be extended. Add features by creating new MCP tools and updating the agent prompt. The architecture is clean and modular.
