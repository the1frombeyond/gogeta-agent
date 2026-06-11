# Installation Guide

## One-liner

**Linux, macOS, WSL, Termux:**

```bash
curl -fsSL https://gogeta.ai/install.sh | bash
```

**Windows (PowerShell 5.1+):**

```powershell
iex (irm https://gogeta.ai/install.ps1)
```

The one-liner handles everything: Python provisioning (via `uv`), cloning the repo, installing dependencies, and registering the `gogeta` command.

### Flags

```bash
curl -fsSL https://gogeta.ai/install.sh | bash -s -- --no-venv     # global install (default)
curl -fsSL https://gogeta.ai/install.sh | bash -s -- --skip-setup  # skip post-install wizard
curl -fsSL https://gogeta.ai/install.sh | bash -s -- --branch dev  # specific branch
```

Windows:

```powershell
iex (irm https://gogeta.ai/install.ps1) -SkipSetup
```

---

## pip / uv

If you already have Python 3.11+ and prefer a pip install:

```bash
pip install gogeta-agent[all]
```

With `uv` (faster):

```bash
uv pip install gogeta-agent[all]
```

The `[all]` extra installs every optional dependency. Replace with `[dev]` for development extras.

---

## Install from source

```bash
git clone https://github.com/the1frombeyond/gogeta-agent.git
cd gogeta-agent
uv pip install -e ".[all,dev]"
```

Or use the automated setup script:

```bash
./setup-gogeta.sh
```

This installs everything (Python, Node, Playwright browsers, skills) into an isolated venv.

---

## Docker

```bash
docker pull ghcr.io/the1frombeyond/gogeta-agent:latest
docker run -it --rm -v gogeta-data:/opt/data ghcr.io/the1frombeyond/gogeta-agent
```

The container uses s6-overlay supervision to run the main agent, dashboard, and per-profile gateways. Mount `/opt/data` to persist config, sessions, and skills.

### Docker Compose

```yaml
services:
  gogeta:
    image: ghcr.io/the1frombeyond/gogeta-agent:latest
    container_name: gogeta
    restart: unless-stopped
    volumes:
      - gogeta-data:/opt/data
    command: ["gateway", "run"]

volumes:
  gogeta-data:
```

For Windows with Docker Desktop, use `docker-compose.windows.yml` from the repo root.

---

## Homebrew

```bash
brew install gogeta-agent
```

---

## Nix

```bash
nix run github:the1frombeyond/gogeta-agent
```

Persistent install:

```bash
nix profile install github:the1frombeyond/gogeta-agent
```

---

## Windows (native, no WSL)

The PowerShell installer supports native Windows without WSL:

```powershell
iex (irm https://gogeta.ai/install.ps1)
```

It provisions `uv` for fast Python management and installs everything under `%LOCALAPPDATA%\gogeta\`. The `gogeta` command is added to your user PATH.

### Desktop GUI

The desktop app (Electron + React) is built as part of the install when you use the bootstrap installer (Gogeta-Setup.exe). For the CLI-only path, run:

```bash
gogeta desktop
```

This builds and launches the desktop app on demand.

---

## Post-install

After any install method:

```bash
gogeta                 # Start your first conversation
gogeta setup           # Full setup wizard (provider, tools, gateway)
gogeta doctor          # Verify the install
gogeta update          # Update to the latest version
```

### Environment variables

GOGETA respects a few key env vars:

| Variable | Default | Description |
|---|---|---|
| `GOGETA_HOME` | `~/.gogeta` | Config, sessions, skills, keys |
| `GOGETA_TUI` | — | Set to `1` to launch TUI by default |
| `GOGETA_BACKGROUND_NOTIFICATIONS` | `all` | Background process verbosity |

---

## Requirements

- **OS:** Linux, macOS 12+, Windows 10+, Android/Termux
- **Python:** 3.11 – 3.13
- **Node:** 20+ (for TUI and desktop)
- **Disk:** ~2 GB (with all deps and Playwright browsers)
- **RAM:** 512 MB minimum, 2 GB+ recommended

No GPU required. GOGETA works with cloud-based inference through any provider.
