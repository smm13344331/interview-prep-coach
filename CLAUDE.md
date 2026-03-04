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
│ - Stateless, data via Core modules                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Core Modules                                                 │
│ - ProgressTracker: learning state                           │
│ - ImprovementLogger: material quality tracking              │
│ - QuestionParser: markdown question parsing                 │
│ - MaterialEditor: copy-on-write material system             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Data Layer                                                   │
│ - XDG-compliant paths (~/.local/share/interview-prep-coach) │
│ - Copy-on-write for bundled material                        │
│ - JSON for progress and improvements                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

**1. Copy-on-Write Material System**
```python
# Bundled material (read-only) in package installation
get_bundled_questions_file() -> Path

# User material (writable) in data directory
get_user_questions_file() -> Path

# Smart selector: prefers user copy over bundled
get_questions_file() -> Path
```

**Why:** Preserves original material, allows user customizations, survives package updates.

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

## Code Structure

```
src/interview_prep_coach/
├── cli.py                      # Entry point: interview-prep-coach command
├── server.py                   # Entry point: interview-prep-coach-server (MCP)
│
├── config/
│   ├── paths.py               # ALL path logic here (XDG-compliant)
│   └── installer.py           # Claude Code integration (skill + MCP)
│
├── core/                      # Business logic (no I/O dependencies)
│   ├── progress.py            # ProgressTracker class
│   ├── improvements.py        # ImprovementLogger class
│   ├── questions.py           # QuestionParser class
│   └── material_editor.py     # MaterialEditor class
│
└── data/                      # Bundled with package (read-only)
    ├── interview-coach-agent-prompt.md      # Agent instructions
    ├── interview-prep-java-spring-infra.md  # Default questions
    ├── learning-progress-template.json
    └── improvement-log-template.json
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

### Resource Access

**For bundled files:**
```python
from interview_prep_coach.config.paths import get_bundled_questions_file

# Python 3.9+ compatible
questions_file = get_bundled_questions_file()
with open(questions_file, 'r') as f:
    content = f.read()
```

### Copy-on-Write Trigger

```python
from interview_prep_coach.config.paths import ensure_editable_material_exists

# Triggers copy if needed
user_material = ensure_editable_material_exists()
# Now safe to modify
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

**Option 1: Replace bundled material**
1. Edit `src/interview_prep_coach/data/interview-prep-java-spring-infra.md`
2. Keep markdown format:
```markdown
## Section Name

### Subsection Name

**Q: Question text?**
Answer text...
```

**Option 2: User customization**
1. User edits `~/.local/share/interview-prep-coach/interview-prep-material.md`
2. System automatically uses it

### Adding New Learning Modes

1. Update agent prompt with new mode behavior
2. Add mode detection in prompt
3. Update skill arguments in `installer.py`
4. No code changes needed!

### Adding New Improvement Types

1. Add to `core/improvements.py`:
```python
"new_type": {
    "count": 0,
    "description": "Description here"
}
```

2. Add handler in `core/material_editor.py` → `apply_improvement()`:
```python
elif improvement_type == 'new_type':
    # Parse and apply logic
    return True, "Applied successfully"
```

3. Update agent prompt to know when to use it

### Adding Analytics

Good places to add:
- `core/progress.py` → track additional metrics
- Add new MCP tool: `get-analytics`
- Store in progress.json under new key
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

This is the bundled question bank. Edit to:
- Add more questions
- Update for new technologies
- Fix errors
- Change focus areas

**After editing:** Rebuild and reinstall.

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

### 5. Copy-on-Write Timing
**Issue:** User copy only created on first edit
**Solution:** This is intentional! Don't pre-create it.

### 6. Progress File Format
**Issue:** If structure changes, old progress files break
**Solution:** Add migration logic in `ProgressTracker.__init__()` or document breaking change

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
├── learning-progress.json        # User progress
├── improvement-log.json          # Logged improvements
└── interview-prep-material.md    # User's editable copy (if modified)
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
from interview_prep_coach.core import ProgressTracker
tracker = ProgressTracker()
progress = tracker.load_progress()
print(progress)
```

### Test material editor
```python
from interview_prep_coach.core import MaterialEditor
editor = MaterialEditor()
info = editor.get_material_info()
print(f"Using: {info['source']}")
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
- Progress file format → Add migration or bump major version
- MCP tool signatures → Update agent prompt + bump minor version
- Question file format → Add backward compat or bump major version

## Security Considerations

- User data stored locally (no network calls)
- Material edits are local only
- No secrets or credentials stored
- Claude Code handles authentication
- MCP server runs locally only

## Performance Notes

- Question parsing: ~20ms (cached after first parse)
- Progress save: ~5-10ms (JSON write)
- Material edit: ~10-20ms (file write)
- First material edit: ~50ms (copies bundled file)

## Future Enhancements Ideas

- [ ] Export progress as PDF report
- [ ] Spaced repetition scheduling
- [ ] Multi-user support with sync
- [ ] Web dashboard for progress
- [ ] Plugin system for custom material sources
- [ ] Integration with Anki/flashcard apps
- [ ] Voice mode for practice
- [ ] Company-specific question banks

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
