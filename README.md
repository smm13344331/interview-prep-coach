# Interview Prep Coach 🎯

AI-powered technical interview preparation system with progress tracking, adaptive learning, and self-improving material.

## Quick Start

```bash
# Install
pip install interview-prep-coach

# Integrate with Claude Code
interview-prep-coach install

# Restart Claude Code and use
/prep
```

## What Is This?

An intelligent interview preparation system that:
- **Plugin-based materials** - Easy to add custom topics, import from files or APIs
- **Database-backed** - Fast searches, persistent tracking, powerful queries
- **Tracks your progress** - Remembers everything across sessions
- **Identifies weak areas** - Focuses practice where you need it
- **Self-improves** - AI coach can enhance the questions based on usage
- **Multiple material sources** - Switch between different question banks

## Features

### 🎓 Interactive Learning
- One-on-one coaching with an AI interviewer
- Conversational Q&A (not flashcards)
- Constructive feedback on your answers
- Teaches concepts when you struggle
- Adaptive difficulty

### 📊 Progress Tracking
- Persistent across sessions
- Accuracy per topic
- Weak/strong area identification
- Session history
- Overall statistics

### 🔄 Self-Improving Material
- Coach notices unclear questions during sessions
- Logs improvement suggestions
- Can apply fixes directly to material
- Material evolves based on real usage

### 🎯 Learning Modes

**Continue Mode** (`/prep`)
- Resume from where you left off
- Linear progression through material

**Weak Areas Mode** (`/prep weak`)
- Focus on topics with <60% accuracy
- Targeted practice

**Mock Interview Mode** (`/prep mock`)
- Random questions across sections
- Simulates real interview conditions
- Formal evaluation

**Section-Specific** (`/prep section <name>`)
- Deep dive into one topic
- Practice specific technology

## Installation

### Prerequisites
- Python 3.10 or higher
- Claude Code (latest version)
- pip

**Note**: SQLite 3.38+ is required to avoid CVE-2022-35737. This is handled automatically via `pysqlite3-binary` dependency - no manual configuration needed.

### Install Package

```bash
pip install interview-prep-coach
```

This automatically installs:
- Core package with CLI and MCP server
- `pysqlite3-binary` (bundles SQLite 3.42+ for security)
- All required dependencies

### Integrate with Claude Code

```bash
interview-prep-coach install
```

This will:
- ✓ Install `/prep` skill in `~/.claude/skills/`
- ✓ Configure MCP server in `~/.claude/settings.json`
- ✓ Initialize data directory at `~/.local/share/interview-prep-coach/`

### Verify Installation

```bash
interview-prep-coach status
```

### Restart Claude Code

Exit and restart Claude Code for changes to take effect:
```bash
exit
claude
```

## Usage

### Start a Session

```bash
/prep                    # Continue from last session
/prep weak              # Practice weak areas
/prep mock              # Mock interview mode
/prep section Docker    # Practice specific section
```

### During a Session

The coach will:
1. Welcome you and show progress
2. Ask questions one at a time
3. Evaluate your answers
4. Provide constructive feedback
5. Track progress automatically
6. Adapt difficulty based on performance

Available commands during practice:
- Type your answer naturally
- `hint` - Get a hint
- `skip` - Skip question
- `explain` - See answer with explanation

### Example Session

```
You: /prep

Coach: Welcome back! 👋

📊 Your Progress:
- Questions answered: 45 (82% correct)
- Current section: Java Core Concepts
- Weak areas: Concurrency, GC Algorithms

What would you like to do?

You: continue

Coach: Great! Let's continue with Java Core Concepts.

Question #5 - Memory Management

Explain the difference between young generation and old generation in Java heap.

---
Take your time. Type your answer when ready.

You: [Your answer here...]

Coach: ✅ Excellent! You covered the key points...
[Provides detailed feedback]

Ready for the next question?
```

## How It Works

### Architecture

```
User types: /prep
     ↓
Claude Code loads skill from: ~/.claude/skills/prep/SKILL.md
     ↓
Coach activates MCP server: interview-prep-coach-server
     ↓
MCP provides 19 tools for:
  - Question management
  - Progress tracking
  - Improvement logging
  - Material editing
     ↓
Data stored locally: ~/.local/share/interview-prep-coach/
```

### MCP Tools (19 Total)

The coach uses these tools automatically:

**Question Management**
- Get next question in sequence
- Search questions by keyword
- List sections and subsections
- Parse questions from material

**Progress Tracking**
- Load/save learning state
- Track accuracy per topic
- Identify weak areas
- Calculate statistics

**Material Improvement**
- Log quality issues
- Apply improvements to questions
- Edit questions directly
- Add new questions

### Data Storage

All your data is stored locally in a SQLite database:

```
~/.local/share/interview-prep-coach/
└── interview-prep.db            # SQLite database (all data)
```

The database contains:
- **materials** - Question sources (bundled, imported, cloned)
- **questions** - All questions with full-text search
- **progress** - Per-question attempt history
- **improvements** - Material quality tracking
- **sessions** - Learning session history
- **plugins** - Plugin registry

**Bundled questions** (imported on first run):
```
/usr/local/lib/.../interview_prep_coach/data/
└── interview-prep-java-spring-infra.md  # Default questions (45KB)
```

**Plugin system**: Add custom materials via plugins or file import. Switch between materials anytime.

## Material Improvement System

The coach can improve its own teaching material!

### How It Works

1. **During session**, coach (or you) notices an issue:
   - Unclear question
   - Outdated information
   - Missing topic
   - Incorrect answer

2. **Coach logs it**:
   ```
   Coach: "I noticed this question mentions outdated version info.
          Should I update it now?"
   ```

3. **If approved**, coach applies fix:
   ```
   ✓ Applied improvement #5: Updated question 3 in Spring Framework
   ```

4. **Next user** gets the improved version!

### Improvement Types

- `unclear_question` - Question is ambiguous
- `answer_issue` - Answer incomplete/wrong
- `outdated_info` - Technology version outdated
- `missing_topic` - Coverage gap
- `insufficient_coverage` - Needs more depth
- `difficulty_mismatch` - Too easy/hard

### You Can Customize

With the plugin and material system:
- Import your own questions from markdown files
- Clone and modify existing materials
- Create custom plugins for different sources
- Switch between material banks anytime
- All changes persist in the database

## CLI Commands

```bash
# Installation
interview-prep-coach install       # Install to Claude Code
interview-prep-coach uninstall     # Remove from Claude Code
interview-prep-coach status        # Show installation & progress
interview-prep-coach info          # System information

# Progress management
interview-prep-coach reset         # Clear progress for active material

# Material management
interview-prep-coach materials list              # List all materials
interview-prep-coach materials info <id>         # Show material details
interview-prep-coach materials activate <id>     # Switch active material
interview-prep-coach materials import <file>     # Import from file
interview-prep-coach materials clone <id> <new>  # Clone for customization
interview-prep-coach materials export -o <file>  # Export to markdown
interview-prep-coach materials delete <id>       # Delete material
```

## Customization

### Import Your Own Material

```bash
# Create a markdown file with your questions (see format below)
# Then import it:
interview-prep-coach materials import my-questions.md \
  --id my-topic \
  --name "My Custom Topic"

# Activate it:
interview-prep-coach materials activate my-topic

# Start practicing:
/prep
```

### Clone and Modify Existing Material

```bash
# Clone bundled material
interview-prep-coach materials clone java-spring-bundled my-java \
  --name "My Java Questions"

# Activate your copy
interview-prep-coach materials activate my-java

# Edit questions via the coach during sessions or export/edit/re-import
interview-prep-coach materials export -o /tmp/my-java.md
# Edit the file...
interview-prep-coach materials import /tmp/my-java.md --id my-java-v2 --name "My Java V2"
```

### Question Format

Questions use simple markdown:

```markdown
## Section Name

### Subsection Name

**Q: Question text here?**
Answer text here with explanations...

**Q: Another question?**
Another answer...
```

The importer automatically parses this format and stores questions in the database.

## Troubleshooting

### SQLite Version Error

If you see an error about SQLite version or CVE-2022-35737:

```bash
# Reinstall to ensure pysqlite3-binary is properly installed
pip install --force-reinstall interview-prep-coach

# Or just reinstall the SQLite package
pip install --force-reinstall pysqlite3-binary
```

Verify the fix:
```bash
python -c "from interview_prep_coach._sqlite_compat import sqlite3; print(f'SQLite: {sqlite3.sqlite_version}')"
# Should show: SQLite: 3.42.0 or higher
```

### `/prep` command not found

1. Check installation: `interview-prep-coach status`
2. Verify skill exists: `ls ~/.claude/skills/prep/SKILL.md`
3. Restart Claude Code completely
4. Check Claude Code version is latest

### MCP server not responding

```bash
# Check settings
cat ~/.claude/settings.json | grep interview-prep-coach

# Should show:
# "interview-prep-coach": {
#   "command": "interview-prep-coach-server",
#   ...
# }
```

### Progress not saving

Check database permissions:
```bash
ls -la ~/.local/share/interview-prep-coach/interview-prep.db
```

If database is corrupted:
```bash
rm ~/.local/share/interview-prep-coach/interview-prep.db
# Restart - will recreate database
```

### Reset everything

```bash
interview-prep-coach reset                      # Clear progress (keeps materials)
interview-prep-coach materials delete <id>      # Delete specific material
interview-prep-coach uninstall --remove-data    # Remove everything including database
pip uninstall interview-prep-coach              # Remove package
```

## Development

### Building from Source

```bash
git clone <repository>
cd interview-prep-coach

# Install in development mode
pip install -e .

# Build package
python -m build

# Install locally
pip install dist/interview_prep_coach-1.0.0-py3-none-any.whl
```

### Project Structure

```
interview-prep-coach/
├── src/interview_prep_coach/
│   ├── cli.py              # Command-line interface
│   ├── server.py           # MCP server (19 tools)
│   ├── config/
│   │   ├── paths.py        # File path management
│   │   └── installer.py    # Claude Code integration
│   ├── core/
│   │   ├── database.py     # DatabaseManager (SQLite)
│   │   ├── schema.py       # Database schema definitions
│   │   ├── progress.py     # ProgressTracker
│   │   ├── improvements.py # ImprovementLogger
│   │   ├── questions.py    # QuestionParser
│   │   ├── material_editor.py    # MaterialEditor
│   │   └── plugin_manager.py     # PluginManager
│   ├── plugins/
│   │   ├── base.py         # MaterialPlugin base class
│   │   ├── importers.py    # MarkdownImporter, JSONImporter
│   │   └── bundled/        # Bundled plugins
│   │       └── java_spring_importer.py
│   └── data/               # Bundled data
│       ├── interview-coach-agent-prompt.md
│       ├── interview-prep-java-spring-infra.md
│       └── schema.sql
└── tests/
```

## Technology Details

### Built With
- [MCP (Model Context Protocol)](https://github.com/anthropics/mcp) - Claude integration
- [Click](https://click.palletsprojects.com/) - CLI interface
- SQLite 3.42+ - Database with FTS5 full-text search (via `pysqlite3-binary`)

### Python Support
- Python 3.10+
- Cross-platform (Linux, macOS, Windows/WSL)
- Bundled SQLite 3.42+ (no system dependency)

### License
MIT License - see LICENSE file

## FAQ

**Q: Is this only for Java/Spring/Docker/Kubernetes?**
A: No! The default material includes those topics, but the system works with ANY technical content. Replace the material with your own questions.

**Q: Does it work offline?**
A: Yes, everything is local. Claude Code requires internet, but your data stays on your machine.

**Q: Can multiple people use it?**
A: Yes, each user has their own progress file. Data is per-user account.

**Q: How does it compare to flashcards?**
A: More interactive! The AI coach evaluates understanding, teaches concepts, adapts difficulty, and has conversations rather than just showing cards.

**Q: Can I export my progress?**
A: Progress is stored in SQLite at `~/.local/share/interview-prep-coach/interview-prep.db`. You can copy the entire database or export materials to markdown using `interview-prep-coach materials export`.

**Q: What happens on package update?**
A: Your database (progress, custom materials, improvements) is preserved. Package updates only affect the bundled code and default material source.

## Contributing

Contributions welcome!

**To improve bundled material:**
1. Use `/prep` and notice issues
2. Let the coach log improvements
3. Export improved version: `interview-prep-coach materials export -o improved.md`
4. Submit as PR to update `data/interview-prep-java-spring-infra.md`

**To add new material plugins:**
1. Create a new plugin class extending `MaterialPlugin`
2. Add to `plugins/bundled/`
3. Submit as PR

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/interview-prep-coach/issues)
- Docs: This README
- Help: `interview-prep-coach --help`

---

**Ready to ace your next interview?** Install now and start practicing! 🚀

```bash
pip install interview-prep-coach && interview-prep-coach install
```
