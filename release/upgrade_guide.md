# Gogeta Upgrade Guide

## Upgrading from Gogeta 2.x / pre-3.0

If you have an existing Gogeta installation, run the installer again:

```bash
curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
```

The installer detects the existing `~/.gogeta` directory and runs `git pull` instead of cloning fresh.

### Post-Upgrade Steps

1. **Update tools configuration**:
   ```bash
   gogeta tools setup
   ```

2. **Update skill indexes**:
   ```bash
   gogeta skills update
   ```

3. **Regenerate TUI build** (if applicable):
   ```bash
   cd ~/.gogeta/ui-tui && npm install && npm run build
   ```

### Breaking Changes (pre-3.0 → 3.0)

| Area | Change |
|------|--------|
| Config | `terminal.cwd` replaces `MESSAGING_CWD` and `TERMINAL_CWD` env vars |
| Plugins | `register(ctx)` signature changed — review plugin code |
| Gateway | Base adapter API updated — custom platform adapters need updates |
| CLI | Slash command registry moved to `gogeta_cli/commands.py` |

## Upgrading from Hermes 2.x

Gogeta 3.0 is a **fresh installation** — there is no automated migration path from Hermes.

1. Install Gogeta 3.0
2. Copy API keys from `~/.hermes/.env` to `~/.gogeta/.env`
3. Copy custom skills from `~/.hermes/skills/` to `~/.gogeta/skills/`
4. Custom plugins must be updated for the new Gogeta plugin API

## Manual Upgrade

To manually upgrade an existing installation:

```bash
cd ~/.gogeta
git pull origin main
source .venv/bin/activate
pip install -e .
cd ui-tui && npm install && npm run build
```

## Verifying the Upgrade

```bash
gogeta --version
# Should show v3.0.0 or later

gogeta doctor
# Should report all systems green
```
