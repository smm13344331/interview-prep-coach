# Interview Prep Coach

> An AI-powered technical interview coach that lives inside Claude Code — tracks your progress, adapts to your weak spots, and improves its own question bank over time.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-lightgrey)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-MCP-purple)](https://claude.ai/claude-code)

Once installed, open Claude Code and type:

```
/prep
```

Your personal interview coach starts immediately — no browser, no separate app.

---

## Why This Exists

Most interview prep tools are passive — flashcards, videos, static PDFs. This is different:

- **Conversational** — a real back-and-forth with an AI coach, not click-through cards
- **Memory** — it remembers every question you've answered, every mistake you've made
- **Adaptive** — `/prep weak` zeros in on topics where your accuracy is below 60%
- **Self-improving** — the coach can rewrite unclear questions mid-session and save the fix permanently
- **Your material** — import any markdown file as a question bank; the system isn't Java/Spring-only

---

## Quick Start

```bash
pip install interview-prep-coach
interview-prep-coach install   # run from the directory where you'll use Claude Code
```

Restart Claude Code, then type inside it:

```
/prep
```

---

## Demo

```
You: /prep

Coach: Welcome back! 📊 Progress: 47 questions answered, 83% correct
       Current section: Java Core — Memory Management
       Weak areas: Concurrency (54%), GC Algorithms (48%)

       Ready to continue?

You: yes

Coach: ─────────────────────────────────────────────
       Question #12 · Memory Management

       Explain the difference between young generation
       and old generation in the Java heap.
       ─────────────────────────────────────────────
       Take your time. Type your answer when ready.

You: Young gen holds short-lived objects and is GC'd frequently
     via minor GC. Old gen holds long-lived objects and is
     collected less often via major/full GC...

Coach: ✅ Solid answer! You nailed the lifecycle distinction.
       One thing to add: survivor spaces (S0/S1) in young gen
       act as a staging area before promotion to old gen.

       Ready for the next one?
```

---

## Features

### Interactive coaching
One-on-one Q&A with a patient, constructive AI interviewer. Not flashcards — real conversations where the coach explains concepts when you're stuck.

### Persistent progress
Every answer is recorded in a local SQLite database. Accuracy per topic, session history, weak areas — all tracked automatically across sessions.

### Adaptive modes
| Command | Mode |
|---|---|
| `/prep` | Continue from where you left off |
| `/prep weak` | Focus on topics under 60% accuracy |
| `/prep mock` | Random questions, formal evaluation |
| `/prep section Docker` | Deep dive into one topic |

### Self-improving material
When the coach notices an unclear question or outdated info during a session, it can propose and apply a fix on the spot. Your next session benefits from the improvement.

### Plugin-based question banks
The default bank covers Java, Spring, Docker, and Kubernetes. Swap it out completely, import your own markdown file, or clone and customize existing material.

---

## Installation

**Prerequisites:** Python 3.10+, Claude Code, pip

```bash
# 1. Install the package
pip install interview-prep-coach

# 2. Register /prep skill and MCP server (run from the directory where you'll open Claude Code)
interview-prep-coach install

# 3. Restart Claude Code, then type inside it:
#    /prep
```

All data is stored locally — no accounts, no cloud sync, no telemetry.

```
~/.local/share/interview-prep-coach/
└── interview-prep.db    ← SQLite: questions, progress, sessions, improvements
```

> **Important: directory-scoped activation**
> Run `interview-prep-coach install` from the directory where you intend to use Claude Code. The MCP server is registered as a project-scoped entry in `~/.claude.json` keyed to that exact path — Claude Code will only activate it when opened in the same directory. If you want `/prep` available in a different directory, `cd` there and run `interview-prep-coach install` again. Your progress database is shared regardless of which directory you install from.

---

## Modes & Commands

### During a session
- Type your answer naturally — the coach evaluates it
- `hint` — get a nudge
- `skip` — move to the next question
- `explain` — see the full answer with explanation

### CLI
```bash
interview-prep-coach status                     # Show install + progress summary
interview-prep-coach materials list             # List all question banks
interview-prep-coach materials import my.md     # Import custom questions
interview-prep-coach materials activate <id>    # Switch active bank
interview-prep-coach materials clone <id> <new> # Fork a bank for customization
interview-prep-coach materials export -o out.md # Export to markdown
interview-prep-coach reset                      # Clear progress (keeps materials)
interview-prep-coach uninstall                  # Remove from Claude Code
```

---

## Bring Your Own Questions

Any markdown file with this structure works:

```markdown
## Section Name

### Subsection Name

**Q: Your question here?**
The answer and explanation here.

**Q: Another question?**
Another answer.
```

Import it:
```bash
interview-prep-coach materials import my-questions.md \
  --id my-topic \
  --name "My Custom Topic"

interview-prep-coach materials activate my-topic
/prep
```

---

## Architecture

```
/prep (Claude Code skill)
  └── interview-prep-coach-server (MCP server, 25 tools)
        ├── QuestionParser   — retrieve & search questions (FTS5)
        ├── ProgressTracker  — per-question attempt history
        ├── ImprovementLogger — log & apply material fixes
        ├── MaterialEditor   — CRUD on question banks
        └── PluginManager    — install/enable/disable plugins
              └── SQLite database (~/.local/share/.../interview-prep.db)
```

The MCP server is stateless — each tool call is independent, all state lives in SQLite. The `/prep` skill is a prompt that instructs Claude to act as a coach using those 25 tools.

---

## How It Works (Under the Hood)

1. `interview-prep-coach install` copies a `SKILL.md` to `~/.claude/skills/prep/` (global) and registers the MCP server in `~/.claude.json` **scoped to the current working directory**
2. When Claude Code starts in that directory, it reads the project entry and launches the MCP server
3. When you type `/prep`, Claude loads the skill prompt and calls MCP tools to get questions, track answers, and log improvements — all locally
4. Progress persists in SQLite between sessions; no data leaves your machine

The directory scope is a Claude Code constraint: MCP servers are configured per-project so different projects can use different tools without conflicts. The side-effect is that `/prep` will silently have no tools if you open Claude Code in a different directory. Re-running `interview-prep-coach install` from any directory adds a new entry for that path.

---

## Troubleshooting

**`/prep` not found or has no tools** — The most common cause is opening Claude Code in a different directory than where you ran `interview-prep-coach install`. The MCP server is directory-scoped (see Installation note). Either `cd` to the original directory, or re-run `interview-prep-coach install` from the current one. Then restart Claude Code.

**MCP server not responding** — Check that the server is registered for the current directory:
```bash
cat ~/.claude.json | grep -A5 interview-prep-coach
```

**SQLite error** — The package bundles SQLite 3.42+ via `pysqlite3-binary` to avoid CVE-2022-35737. If you see an error:
```bash
pip install --force-reinstall pysqlite3-binary
```

**Reset everything**
```bash
interview-prep-coach uninstall --remove-data
pip uninstall interview-prep-coach
```

---

## FAQ

**Is this only for Java/Spring?**
No. The default material covers Java, Spring, Docker, and Kubernetes. Replace it with any markdown file and it works for any technical topic.

**Does it require internet?**
Claude Code requires internet. Your data (questions, progress, improvements) stays entirely local.

**Does it work on macOS / Windows?**
Linux and macOS natively. Windows via WSL.

**Can I export my question bank or back up my data?**

Export the active question bank to markdown:
```bash
interview-prep-coach materials export -o questions.md
```

Back up everything (questions, progress, session history):
```bash
cp ~/.local/share/interview-prep-coach/interview-prep.db ~/backup.db
```

---

## Contributing

**Improve the bundled question bank:**
1. Use `/prep` and let the coach log improvements
2. Export: `interview-prep-coach materials export -o improved.md`
3. Submit a PR updating `src/interview_prep_coach/data/interview-prep-java-spring-infra.md`

**Add a new topic plugin:**
1. Subclass `MaterialPlugin` in `src/interview_prep_coach/plugins/bundled/`
2. Submit a PR

See [CLAUDE.md](CLAUDE.md) for the full development guide.

---

## Built With

- [MCP (Model Context Protocol)](https://github.com/anthropics/mcp) — Claude tool integration
- [Click](https://click.palletsprojects.com/) — CLI
- [SQLite + FTS5](https://www.sqlite.org/fts5.html) — local database with full-text search (bundled via `pysqlite3-binary`)

---

MIT License · [Issues](https://github.com/smm13344331/interview-prep-coach/issues)

```bash
pip install interview-prep-coach && interview-prep-coach install
```
