# Interview Prep Coach - Distribution Package

## Quick Install

```bash
./install.sh
```

That's it! The installer will:
- Check all prerequisites
- Install the package
- Configure Claude Code integration
- Verify the installation

## Requirements

- Linux system (Ubuntu, Debian, Fedora, etc.)
- Python 3.10 or higher
- pip (Python package manager)
- Claude Code (installed and configured)

## Package Contents

```
interview-prep-coach/
├── install.sh                     # Main installer script
├── dist/
│   └── interview_prep_coach-1.0.0-py3-none-any.whl  # Python package
├── README.md                      # Full documentation
└── DISTRIBUTION.md                # This file
```

## Installation Steps

### 1. Extract Package

```bash
tar -xzf interview-prep-coach-1.0.0.tar.gz
cd interview-prep-coach
```

### 2. Run Installer

```bash
./install.sh
```

The installer will:
1. ✓ Check Python 3.10+ is installed
2. ✓ Check pip is available
3. ✓ Check for the wheel package
4. ✓ Check Claude Code directory exists
5. ✓ Install the Python package
6. ✓ Verify installation
7. ✓ Configure Claude Code integration

### 3. Restart Claude Code

**Important:** Restart Claude Code for changes to take effect.

### 4. Use It

```bash
claude
> /prep
```

## Manual Installation

If you prefer manual installation:

```bash
# Install package
pip3 install dist/interview_prep_coach-1.0.0-py3-none-any.whl

# Configure Claude Code
interview-prep-coach install

# Restart Claude Code
```

## Uninstall

```bash
./install.sh uninstall
```

Or manually:

```bash
interview-prep-coach uninstall
pip3 uninstall interview-prep-coach
```

## Usage

### In Claude Code

```
/prep                    # Continue last session
/prep weak              # Practice weak areas
/prep mock              # Mock interview mode
/prep section Java      # Practice specific section
```

### Command Line

```bash
interview-prep-coach status             # Check installation
interview-prep-coach materials list     # List available materials
interview-prep-coach materials import   # Import custom materials
```

## Portability

✅ **Fully Portable** - Works on any Linux system with Python 3.10+

- No root/sudo required
- User-level installation
- XDG-compliant data storage
- No hardcoded paths
- Bundled SQLite (no system dependencies)

## Data Locations

After installation:
- Database: `~/.local/share/interview-prep-coach/interview-prep.db`
- Skills: `~/.claude/skills/prep/SKILL.md`
- MCP Config: `~/.claude.json` (project-scoped)

## Troubleshooting

### Python Version Check
```bash
python3 --version  # Must be 3.10+
```

### Install pip
```bash
sudo apt install python3-pip  # Ubuntu/Debian
sudo dnf install python3-pip  # Fedora
```

### Check Installation
```bash
interview-prep-coach status
```

### Verify Commands
```bash
which interview-prep-coach
which interview-prep-coach-server
```

### PATH Issues

If commands not found, add to PATH:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Support

For issues:
1. Check `interview-prep-coach status`
2. Ensure Python 3.10+ is installed
3. Verify Claude Code is installed
4. Check logs in `~/.local/share/interview-prep-coach/`
