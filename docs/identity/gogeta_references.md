# Gogeta Reference Catalog

> **Audit Date:** 2026-06-08
> **Scope:** Every "Gogeta", "gogeta", "GOGETA" occurrence in `Downloads/gogeta/`

## Summary

| Category | File Count | Approx. Reference Count |
|----------|-----------|------------------------|
| **`gogeta_cli/` packages** | ~100 files | 3,966+ |
| **Root files** | 8 files | 337+ |
| **`agent/`** | ~30 files | 643+ |
| **`gateway/`** | ~20 files | 565+ |
| **`tui_gateway/`** | 3 files | 124+ |
| **`ui-tui/`** | ~40 files | 152+ |
| **`core/`** | 1 file | 3 |
| **`gogeta/`** | 1 file | 2 |
| **`pyproject.toml`** | 1 file | 36 |
| **`package.json`** | 1 file | 1 |
| **`tests/gogeta_cli/`** | 309 files | ~3,000+ |
| **Total** | **~514+ files** | **~8,829+ references** |

---

## 1. File Renames Required

### Root-level files that reference "gogeta" in their name:

| Current Name | Rename To | Reason |
|-------------|-----------|--------|
| `gogeta_cli/` | `gogeta_cli/` | Main CLI package |
| `gogeta_constants.py` | `gogeta_constants.py` | Constants module |
| `gogeta_bootstrap.py` | `gogeta_bootstrap.py` | Windows UTF-8 bootstrap |
| `gogeta_logging.py` | `gogeta_logging.py` | Logging setup |
| `gogeta_state.py` | `gogeta_state.py` | Session DB state |
| `gogeta_time.py` | `gogeta_time.py` | Timezone utils |
| `gogeta` (binary) | `gogeta` (binary) | CLI entry point script |
| `setup-gogeta.sh` | `setup-gogeta.sh` | Install script |
| `gogeta-already-has-routines.md` | `gogeta-routines.md` | Doc |

### Test directory rename:
| Current | Rename To |
|---------|-----------|
| `tests/gogeta_cli/` | `tests/gogeta_cli/` |

---

## 2. Reference Type Breakdown

### A. Import paths (most numerous, ~4,500+ refs)
All `from gogeta_cli.xxx import yyy` and `from gogeta_constants import ...` patterns across the codebase. Every `.py` file in `agent/`, `gateway/`, `tui_gateway/`, `core/`, and `gogeta/` that imports from these packages.

### B. Package names in pyproject.toml (~36 refs)
- `name = "gogeta-agent"`
- `gogeta = "gogeta_cli.main:main"`
- `gogeta-agent = "run_agent:main"`
- `gogeta-acp = "acp_adapter.entry:main"`
- Extras: `"gogeta-agent[cron]"`, `"gogeta-agent[cli]"`, etc.
- `py-modules` list: `gogeta_bootstrap`, `gogeta_constants`, `gogeta_state`, `gogeta_time`, `gogeta_logging`
- Wheel includes: `gogeta_cli = ["web_dist/**/*", ...]`

### C. Package name in package.json
- `"name": "gogeta-agent"`

### D. GOGETA_HOME env var (~200+ refs)
Used throughout for config directory resolution:
- `os.environ.get("GOGETA_HOME")`
- `get_gogeta_home()` (gogeta_constants function)
- `set_gogeta_home_override()`, `reset_gogeta_home_override()`, `get_gogeta_home_override()`
- `~/.gogeta/` path references
- `%LOCALAPPDATA%\\gogeta` (Windows path)

### E. Class names (~50+ refs)
- `GsaCLI` (main CLI class in cli.py)
- References in `gogeta_cli.commands.COMMAND_REGISTRY`
- References as `Gogeta State` or `Gogeta` in user-facing text

### F. CLI command references in help text (~200+ refs)
- `` `gogeta` `` in docstrings and help messages
- `` `gogeta setup` ``, `` `gogeta model` ``, `` `gogeta update` ``, etc.
- `` `gogeta chat -q` ``
- `` `gogeta gateway` ``
- `` `gogeta doctor` ``
- `` `gogeta status` ``
- `` `gogeta auth add ...` ``
- `` `gogeta proxy start` ``
- `` `gogeta --help` ``
- `` `gogeta -w` `` (worktree mode)

### G. @gogeta/ink package references (~100+ refs)
In `ui-tui/src/`, every React component imports from `@gogeta/ink` (custom fork of Ink).

### H. Internal sentinel attributes (~30+ refs)
- `_gogeta_bp_timeout_patched`
- `_gogeta_bp_start`
- `_gogeta_ipv4_patched`
- `_gogeta_verbose`
- `_gogeta_light_mode_hook_installed`
- `_gogeta_session_injector`

### I. Internal constant names (~20+ refs)
- `_GOGETA_CORE_TOOLS` (in SKILL.md, not in source)
- `GOGETA_ARCHIVE_DIRS`, `GOGETA_ARCHIVE_FILES` (in openclaw plugin)

### J. Cookie names (~6 refs)
- `gogeta_session_at`, `gogeta_session_rt`, `gogeta_session_pkce`

### K. Config paths and paths in comments/docs (~400+ refs)
- `~/.gogeta/config.yaml`
- `~/.gogeta/.env`
- `~/.gogeta/skills/`
- `~/.gogeta/logs/`
- `~/.gogeta/sessions/`
- `~/.gogeta/state.db`
- `~/.gogeta/perf.log`
- `~/.gogeta/heapdumps/`
- `~/.gogeta/events/`
- `~/.gogeta/cache/`
- `~/.gogeta/checkpoints/`
- `~/.gogeta/plans/`
- `~/.gogeta/spawn-trees/`

### L. User-facing branding (~100+ refs)
- "gogeta" in startup banners
- "gogeta" in help text
- "gogeta" in status displays
- "Exit gogeta" text
- "Exit and run `gogeta setup` manually"
- Error messages suggesting `gogeta setup`
- `~/.gogeta_history` path

### M. Module __init__ exports (~30+ refs)
- `from gogeta_cli import __version__ as _version`
- `from gogeta_cli import __release_date__ as _release_date`
- Various `gogeta_cli.__init__` re-exports

### N. Logger and component names (~20+ refs)
- `"gogeta_cli"` in logging component filters
- `"gogeta_cli.web_server"`
- `"gogeta_cli.pty_bridge"`
- `"tui_gateway.*"`
- `"gogeta_gateway_transport"` (transport name)

### O. Docker container references
- `Dockerfile` CMD references to gogeta
- `docker-compose.yml` service names

---

## 3. Context-Specific Reference Groups

### User-facing text (must change display strings)
File: `gogeta_cli/main.py`, `cli.py`, `setup.py`, `banner.py`
- `"gogeta command"`, `"run gogeta"`, `"gogeta setup"`, `"Exit gogeta"`
- `"cd into your project repo first, then run gogeta -w"`
- `"gogeta git branch pattern"`, `"gogeta-*"` worktree names
- `"Opt back out: gogeta config set compression.codex_gpt55_autoraise false"`

### Internal-only references (can stay as aliases)
- `gogeta_constants` module functions (will be renamed to `gogeta_constants`)
- Python module paths (`gogeta_cli.*` → `gogeta_cli.*`)
- Sentinel attributes (`_gogeta_*` → `_gogeta_*`)

### Cookie names (breaking change, needs migration)
- `gogeta_session_at`, `gogeta_session_rt`, `gogeta_session_pkce`
- Must rename in cookie-setting middleware AND in the auth middleware that reads them
- Old cookies must either redirect or be cleaned up

### localStorage keys (ui-tui)
- `gogeta-web-state` (in gogeta-web, separate project)
- No localStorage keys found in ui-tui/ with "gogeta" prefix

### @gogeta/ink package (ui-tui dependency)
- All 40+ files import from `@gogeta/ink`
- This is the custom forked Ink renderer — the package itself must be renamed
- Package lives in `node_modules/@gogeta/ink` → would need npm publish under new org

### Session file naming
- `gogeta_conversation_{timestamp}.json` (tui_gateway/server.py)
- Worktree branches: `gogeta/gogeta-*` (cli.py)

---

## 4. Scope Boundaries

### NOT in scope for TUI redesign (separate projects):
- `gogeta-web/` — separate web application
- `.agents/skills/gogeta-agent/` — external Gogeta skill definition
- `Documents/ATHOS/` — competitor comparison docs
- `.openclaw/` — OpenClaw migration plugin (external)
- `Documents/GOGETA/sdk/` — installer references to `--gogeta` flag
- `jarvis/` — separate project
- `.ollama/` — unrelated config

### IN SCOPE for TUI redesign (this project):
- `gogeta_cli/` → `gogeta_cli/` and all its contents (~100 files)
- `gogeta_constants.py`, `gogeta_bootstrap.py`, `gogeta_logging.py`, `gogeta_state.py`, `gogeta_time.py`
- `cli.py` (the main entry point)
- `gogeta` (binary script)
- `setup-gogeta.sh`
- `ui-tui/` (~40 files with `@gogeta/ink` imports)
- `tui_gateway/` (~3 files, 124 refs)
- `agent/` (~30 files, 643 refs)
- `gateway/` (~20 files, 565 refs)
- `core/` (1 file, 3 refs)
- `gogeta/` (1 file, 2 refs)
- `pyproject.toml`, `package.json`
- `tests/gogeta_cli/` (309 files, ~3,000 refs)
