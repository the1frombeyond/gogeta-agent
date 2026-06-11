# Branding Audit: Gogeta → Gogeta 3.0

> **Audit Date:** 2026-06-08
> **Scope:** All user-facing branding, visual identity, and naming in the project

---

## 1. Brand Identity

### Current State: Gogeta Agent
- Package: `gogeta-agent`
- CLI command: `gogeta`
- Config directory: `~/.gogeta/`
- Env var: `GOGETA_HOME`
- Logo/herald: Winged sandal (Gogeta mythology)
- Nickname: "The AI Agent Framework"

### Target State: Gogeta 3.0
- Package: `gogeta-agent` (or `gogeta`)
- CLI command: `gogeta`
- Config directory: `~/.gogeta/`
- Env var: `GOGETA_HOME`
- Visual identity: Dragon fusion motif (gold + white ANSI theme)
- Nickname: "The Fusion AI Agent"

---

## 2. Branding Touchpoints Required

### Critical (user-facing every session):

| Touchpoint | Current | Target |
|------------|---------|--------|
| CLI binary name | `gogeta` | `gogeta` |
| Startup banner | `Gogeta Agent vX.Y.Z` | `Gogeta 3.0 vX.Y.Z` |
| Help text | `` `gogeta --help` `` | `` `gogeta --help` `` |
| Error messages | "Run `gogeta setup`" | "Run `gogeta setup`" |
| Prompt prefix | `gogeta>` | `gogeta>` |
| Exit message | "Exiting gogeta" | "Exiting gogeta" |
| Status display | "Gogeta status" | "Gogeta status" |
| Version output | `gogeta version` | `gogeta version` |
| Update command | `gogeta update` | `gogeta update` |
| Package name | `gogeta-agent` | `gogeta-agent` |

### Secondary (per-session):

| Touchpoint | Current | Target |
|------------|---------|--------|
| Config dir | `~/.gogeta/` | `~/.gogeta/` |
| History file | `~/.gogeta/.gogeta_history` | `~/.gogeta/.gogeta_history` |
| Session files | `gogeta_conversation_*.json` | `gogeta_conversation_*.json` |
| Worktree names | `gogeta-*` | `gogeta-*` |
| Branch names | `gogeta/gogeta-*` | `gogeta/gogeta-*` |
| Session DB | `state.db` in `~/.gogeta/` | `state.db` in `~/.gogeta/` |
| Transport name | `gogeta_gateway_transport` | `gogeta_gateway_transport` |

### Tertiary (infrequent/developer):

| Touchpoint | Current | Target |
|------------|---------|--------|
| MCP server name | `gogeta-tools` | `gogeta-tools` |
| LSP name | `gogeta-lsp-loop` | `gogeta-lsp-loop` |
| Bitwarden prefix | `gogeta-bws-*`, `gogeta_home` | `gogeta-bws-*`, `gogeta_home` |
| Crash log | `tui_gateway_crash.log` | (keep, not gogeta-named) |
| Docker service | `gogeta-gateway` | `gogeta-gateway` |
| Venv | `<project>/venv/bin/gogeta` | `<project>/venv/bin/gogeta` |
| Plugin event prefix | `gogeta_cli.*` | `gogeta_cli.*` |

---

## 3. Visual Identity

### Current: Gogeta
- ANSI color scheme: Blue/cyan primary (`#58a6ff`), white secondary
- Banner: Gogeta Agent ASCII art
- Sky/sandal motifs

### Target: Gogeta 3.0
- **Primary:** Gold `#FFD700` / `#e3b341`
- **Secondary:** White `#FFFFFF` / light gray `#E0E0E0`
- **Accent:** Warm amber `#FF8C00`
- **Dim/footer:** Dark gray `#666666`
- **Banner:** Gogeta ASCII art — fusion flame / dragon star motif
- **Theme name:** "Super Saiyan God" or "Fusion"

### Skin Engine Changes
- File: `gogeta_cli/skin_engine.py` (926 lines)
- Skin format: YAML-based, data-driven (no engine rewrite needed)
- Action: Create `gogeta-gold` skin in the skin registry
- Action: Set `gogeta-gold` as the default skin
- Action: Ensure gold/white ANSI 256-color escape sequences

---

## 4. UI Component Branding Audit

### Startup Banner (`gogeta_cli/banner.py`)
```
Current: "Gogeta Agent vX.Y.Z — The AI Agent Framework"
Target:  "Gogeta 3.0 — The Fusion AI Agent"
```

### Help Text (`gogeta_cli/main.py`, `cli.py`, `commands.py`)
- Every occurrence of `` `gogeta <subcommand>` `` must be replaced
- Every `gogeta --flag` reference
- Every `Run gogeta` instruction
- Every `Exit gogeta` or `exit gogeta` text

### Status Bar (`gogeta_cli/cli.py`, `ui-tui/src/components/appChrome.tsx`)
- Status line showing model, provider, session ID — rebrand label
- Add: Header bar with Model | Provider | Session | Cost | Tokens | Genome | Path

### Command Palette (`gogeta_cli/commands.py`)
- Currently named "Gogeta Commands" → "Gogeta Commands"  
- CommandDef category labels may contain "gogeta" references

### Footer / Help Hint (`ui-tui/src/components/helpHint.tsx`)
- `['/quit', 'exit gogeta']` → `['/quit', 'exit gogeta']`

### Skill/Tool Catalog display
- Currently lists "Gogeta skills" on startup — replace with live dashboard

---

## 5. @gogeta/ink Package Assessment

The `@gogeta/ink` package is a custom fork of Vercel's Ink (React renderer for CLIs).

- **Not visible to users** — it's an npm dependency, not a brand touchpoint
- Used in all 40+ `ui-tui/src/` files via imports like `import { Box, Text } from '@gogeta/ink'`
- Renaming would require republishing to npm under a new org/scope

**Recommendation:** Keep `@gogeta/ink` as-is. The internal rendering engine name does not affect user-facing branding. Renaming it is a separate, lower-priority effort.

---

## 6. TUI Gateway Branding

`tui_gateway/server.py` (~7,000 lines):
- All `from gogeta_cli.*` imports → rename automatically with Phase B
- All `from gogeta_constants` → rename automatically with Phase B
- All `_gogeta_home` local variables → rename to `_gogeta_home`
- Help text strings like `"gogeta model"` → `"gogeta model"`
- Session export filenames: `gogeta_conversation_*.json` → `gogeta_conversation_*.json`
- Transport name: `gogeta_gateway_transport` → `gogeta_gateway_transport`
- Path references: `~/.gogeta/` → `~/.gogeta/`

**No architecture changes needed** — purely mechanical renaming.

---

## 7. Agent Subsystem Branding

`agent/` (~643 references):
- All imports follow the package rename (Phase B)
- Config path references (`~/.gogeta/*`) → `~/.gogeta/*`
- CLI command references in error messages
- MCP server name: `gogeta-tools` → `gogeta-tools`
- `_get_gogeta_version()` → `_get_gogeta_version()`
- `client_name="gogeta"` → `client_name="gogeta"`

---

## 8. Gateway Subsystem Branding

`gateway/` (~565 references):
- All imports follow the package rename (Phase B)
- Docker service naming
- Plugin loading paths

---

## 9. PyPI / Distribution Branding

`pyproject.toml`:
- `name = "gogeta-agent"` → `name = "gogeta-agent"`
- Console scripts: `gogeta` → `gogeta`, `gogeta-agent` → `gogeta-agent`, `gogeta-acp` → `gogeta-acp`
- Extras: all `gogeta-agent[xxx]` → `gogeta-agent[xxx]`
- `py-modules`: rename all gogeta_* → gogeta_*
- Include patterns: `gogeta_cli` → `gogeta_cli`

---

## 10. Feature Flag / Config Glossary

### Config keys (in ~/.gogeta/config.yaml)
- `security.redact_secrets` — keep as-is (not gogeta-specific)
- `approvals.mode` — keep as-is

### Environment variables to rename
| Old | New | Accept Old as Fallback? |
|-----|-----|------------------------|
| `GOGETA_HOME` | `GOGETA_HOME` | Yes (6-month deprecation) |
| `GOGETA_IGNORE_USER_CONFIG` | `GOGETA_IGNORE_USER_CONFIG` | Yes |
| `GOGETA_DEV_PERF` | `GOGETA_DEV_PERF` | Yes |
| `GOGETA_DEV_PERF_LOG` | `GOGETA_DEV_PERF_LOG` | Yes |
| `GOGETA_HEAPDUMP_DIR` | `GOGETA_HEAPDUMP_DIR` | Yes |
| `GOGETA_BIN` | `GOGETA_BIN` | Yes |
| `GOGETA_YOLO_MODE` | `GOGETA_YOLO_MODE` | Yes |

### Config directory helpers (in gogeta_constants.py)
| Function | New Name |
|----------|----------|
| `get_gogeta_home()` | `get_gogeta_home()` |
| `get_config_path()` | `get_gogeta_config_path()` |
| `get_gogeta_dir()` | `get_gogeta_dir()` |
| `get_default_gogeta_root()` | `get_default_gogeta_root()` |
| `get_skills_dir()` | `get_gogeta_skills_dir()` |
| `get_optional_skills_dir()` | `get_gogeta_optional_skills_dir()` |
| `get_optional_mcps_dir()` | `get_gogeta_optional_mcps_dir()` |
| `get_default_env_path()` | `get_gogeta_default_env_path()` |

---

## 11. Priority Matrix

| Effort | Impact | Items |
|--------|--------|-------|
| **High Impact, Low Effort** | Quick wins | CLI binary name, startup banner, help text, error messages, prompt prefix |
| **High Impact, Medium Effort** | Core identity | Package rename, ENV var rename, config dir rename, skin theme |
| **Medium Impact, Medium Effort** | Visible but internal | Cookie names, session filenames, branch/worktree names, logger names |
| **Low Impact, High Effort** | Defer | @gogeta/ink rename, backward compat shims, full test sweep |
| **No Impact** | Skip | 3rd-party docs (ATHOS), OpenClaw migration plugin, external skill definitions |

---

## 12. Anti-Patterns to Avoid

1. **Don't rename `@gogeta/ink`** — it's an internal rendering engine, invisible to users; massive effort for zero brand benefit
2. **Don't break existing installs** — support `GOGETA_HOME` as fallback for 6 months; symlink `~/.gogeta` → `~/.gogeta`
3. **Don't rename in a single massive commit** — 514+ files cannot be reviewed meaningfully
4. **Don't rename cookie names without a migration** — existing sessions will be invalidated
5. **Don't change the skin engine architecture** — data-driven YAML skins can be swapped without rewriting
6. **Don't touch setup wizard logic** (`setup.py`, 3,361 lines) — preserves keyboard flow, multi-select, interaction — only rename text strings
