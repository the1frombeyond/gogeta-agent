# Gogeta Installation Guide

## One-Command Install

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
```

Or with `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
iex (iwr https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1).Content
```

## What the Installer Does

1. **Prerequisite check** — verifies Python 3.11+, Git, and Node.js/npm
2. **Clone or update** — clones the repository to `~/.gogeta` (or pulls latest if already installed)
3. **Python environment** — creates a `.venv` virtual environment and installs all dependencies
4. **TUI build** — builds the Ink-based Terminal User Interface
5. **Launcher** — creates a `gogeta` command on your PATH:
   - Linux/macOS: `~/.local/bin/gogeta` (symlink to venv)
   - Windows: `%USERPROFILE%\.gogeta\bin\gogeta.cmd`
6. **PATH setup** — adds the launcher directory to your user PATH

## Post-Install

Run Gogeta:

```bash
gogeta
```

For the Terminal UI:

```bash
gogeta --tui
```

Run the setup wizard to configure API keys:

```bash
gogeta setup
```

## System Requirements

| Component | Minimum |
|-----------|---------|
| Python | 3.11 – 3.13 |
| Git | Any modern version |
| Node.js | 18+ (for TUI build) |
| npm | 9+ |
| RAM | 4 GB (8 GB recommended) |
| Disk | 2 GB free |

## Platform Support

| Platform | Status |
|----------|--------|
| Linux (x86_64) | Full support |
| Linux (aarch64) | Full support |
| macOS (Intel) | Full support |
| macOS (Apple Silicon) | Full support |
| Windows (x86_64) | Full support |
| Android (Termux) | Full support (use `termux` extra) |
