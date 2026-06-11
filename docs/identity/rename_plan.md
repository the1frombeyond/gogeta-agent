# Rename Plan: Gogeta → Gogeta

> **Objective:** Replace all "Gogeta"/"gogeta"/"GOGETA" identifiers in the project with "Gogeta"/"gogeta"/"GOGETA"
> **Strategy:** Systematic, phased, test-verified rename across ~514 files and ~8,800+ references

---

## Rename Phases

### Phase A: Package & Module Names (foundational — unblocks all import paths)

**Files to rename physically:**
| Old Path | New Path |
|----------|----------|
| `gogeta_cli/` | `gogeta_cli/` |
| `gogeta_constants.py` | `gogeta_constants.py` |
| `gogeta_bootstrap.py` | `gogeta_bootstrap.py` |
| `gogeta_logging.py` | `gogeta_logging.py` |
| `gogeta_state.py` | `gogeta_state.py` |
| `gogeta_time.py` | `gogeta_time.py` |
| `gogeta` (binary) | `gogeta` (binary) |
| `setup-gogeta.sh` | `setup-gogeta.sh` |
| `tests/gogeta_cli/` | `tests/gogeta_cli/` |

**Changes in pyproject.toml:**
- `name = "gogeta-agent"` → `name = "gogeta-agent"`
- `gogeta = "gogeta_cli.main:main"` → `gogeta = "gogeta_cli.main:main"`
- `gogeta-agent = "run_agent:main"` → `gogeta-agent = "run_agent:main"`
- `gogeta-acp = "acp_adapter.entry:main"` → `gogeta-acp = "acp_adapter.entry:main"`
- Extras: all `"gogeta-agent[xxx]"` → `"gogeta-agent[xxx]"`
- `py-modules`: rename gogeta_* entries to gogeta_*
- `include = ["gogeta_cli", "gogeta_cli.*", ...]` → `["gogeta_cli", "gogeta_cli.*", ...]`

**Changes in pyproject.toml and package.json:**
- `package.json`: `"name": "gogeta-agent"` → `"name": "gogeta-agent"`

---

### Phase B: Import Path Sweep (~4,500+ references)

Mechanical find-and-replace across all `.py` files:
- `from gogeta_cli.` → `from gogeta_cli.`
- `import gogeta_cli` → `import gogeta_cli`
- `from gogeta_constants` → `from gogeta_constants`
- `from gogeta_state` → `from gogeta_state`
- `from gogeta_logging` → `from gogeta_logging`
- `from gogeta_time` → `from gogeta_time`
- `from gogeta_bootstrap` → `from gogeta_bootstrap`

---

### Phase C: GOGETA_HOME → GOGETA_HOME (~200+ references)

This is the most impactful internal change. Replace:
- Environment variable: `GOGETA_HOME` → `GOGETA_HOME`
- Config directory: `~/.gogeta/` → `~/.gogeta/`
- Functions: `get_gogeta_home()` → `get_gogeta_home()`
- `set_gogeta_home_override()` → `set_gogeta_home_override()`
- `reset_gogeta_home_override()` → `reset_gogeta_home_override()`
- `get_gogeta_home_override()` → `get_gogeta_home_override()`
- `_get_platform_default_gogeta_home()` → `_get_platform_default_gogeta_home()`
- `display_gogeta_home()` → `display_gogeta_home()`
- `get_default_gogeta_root()` → `get_default_gogeta_root()`

**All config directory paths must change:**
| Old Path | New Path |
|----------|----------|
| `~/.gogeta/` | `~/.gogeta/` |
| `~/.gogeta/config.yaml` | `~/.gogeta/config.yaml` |
| `~/.gogeta/.env` | `~/.gogeta/.env` |
| `~/.gogeta/skills/` | `~/.gogeta/skills/` |
| `~/.gogeta/logs/` | `~/.gogeta/logs/` |
| `~/.gogeta/sessions/` | `~/.gogeta/sessions/` |
| `~/.gogeta/state.db` | `~/.gogeta/state.db` |
| `~/.gogeta/cache/` | `~/.gogeta/cache/` |
| `~/.gogeta/events/` | `~/.gogeta/events/` |
| `~/.gogeta/checkpoints/` | `~/.gogeta/checkpoints/` |
| `~/.gogeta/perf.log` | `~/.gogeta/perf.log` |
| `~/.gogeta/heapdumps/` | `~/.gogeta/heapdumps/` |
| `~/.gogeta/spawn-trees/` | `~/.gogeta/spawn-trees/` |
| `~/.gogeta/.gogeta_history` | `~/.gogeta/.gogeta_history` |
| `%LOCALAPPDATA%\\gogeta` | `%LOCALAPPDATA%\\gogeta` |

---

### Phase D: @gogeta/ink → @gogeta/ink (~100+ references in ui-tui/)

All 40+ ui-tui source files import from `@gogeta/ink`. This is a custom fork. Options:
1. **Rename the package** in the Ink renderer fork and republish
2. **Keep @gogeta/ink as a dependency** (it's an internal rendering engine, not user-facing branding)
3. **Create @gogeta/ink** as a wrapper/alias

**Recommendation:** Option 2 (keep `@gogeta/ink` as internal dependency) for now. The package name `@gogeta/ink` is never visible to end users; it's an npm dependency. Renaming it is a separate effort.

---

### Phase E: Sentinel Attributes (~30+ references)

Replace internal sentinel attribute names:
| Old | New |
|-----|-----|
| `_gogeta_bp_timeout_patched` | `_gogeta_bp_timeout_patched` |
| `_gogeta_bp_start` | `_gogeta_bp_start` |
| `_gogeta_ipv4_patched` | `_gogeta_ipv4_patched` |
| `_gogeta_verbose` | `_gogeta_verbose` |
| `_gogeta_light_mode_hook_installed` | `_gogeta_light_mode_hook_installed` |
| `_gogeta_session_injector` | `_gogeta_session_injector` |

---

### Phase F: Cookie Names (~6 references)

| Old | New |
|-----|-----|
| `gogeta_session_at` | `gogeta_session_at` |
| `gogeta_session_rt` | `gogeta_session_rt` |
| `gogeta_session_pkce` | `gogeta_session_pkce` |

**Note:** Must update BOTH the setter (cookies.py) AND the reader (middleware.py). Existing sessions will break — old cookies must be cleaned up or redirected.

---

### Phase G: User-Facing Text (~300+ references)

Replace in help strings, banner text, error messages, docstrings:
- `"gogeta "` → `"gogeta "` (CLI command references like `gogeta setup`)
- `"Gogeta"` → `"Gogeta"` (brand names)
- `"run gogeta"` → `"run gogeta"`
- `"Exit gogeta"` → `"Exit gogeta"`
- Worktree names: `"gogeta-*"` → `"gogeta-*"`
- Branch names: `"gogeta/gogeta-*"` → `"gogeta/gogeta-*"`
- `"gogeta_conversation_*.json"` → `"gogeta_conversation_*.json"`
- `"gogeta-tools"` → `"gogeta-tools"` (MCP server name)

---

### Phase H: Logger Names (~15 references)

- `"gogeta_cli"` → `"gogeta_cli"`
- `"gogeta_cli.web_server"` → `"gogeta_cli.web_server"`
- `"gogeta_cli.pty_bridge"` → `"gogeta_cli.pty_bridge"`
- `"gogeta_gateway_transport"` → `"gogeta_gateway_transport"`

---

### Phase I: Test File Contents (~309 files, ~3,000+ references)

All test files in `tests/gogeta_cli/` reference `gogeta_cli.*` imports and CLI commands. These change automatically when the source package is renamed — BUT must be swept independently since many tests assert on CLI output strings, help text, and path names.

---

## Execution Strategy

### Wave 1: Source rename + pyproject.toml
1. Rename files (`gogeta_cli/` → `gogeta_cli/`, etc.)
2. Update `pyproject.toml` and `package.json`
3. Replace all `gogeta_cli.*` and `gogeta_constants` imports

### Wave 2: GOGETA_HOME → GOGETA_HOME
4. Update `gogeta_constants.py` (was gogeta_constants.py)
5. Replace all env var, function, and path references
6. Create migration script or symlink `~/.gogeta` → `~/.gogeta`

### Wave 3: User-facing text + branding
7. Replace CLI help text, error messages, docstrings
8. Replace cookie names
9. Replace sentinel attributes
10. Replace logger names

### Wave 4: Tests
11. Update all 309 test files
12. Run full test suite
13. Fix any failures

---

## Migration Compatibility

### Backward Compatibility Strategy
- **Config directory:** Symlink `~/.gogeta` → `~/.gogeta` so existing configs still work
- **GOGETA_HOME env var:** Accept `GOGETA_HOME` as fallback if `GOGETA_HOME` not set
- **Cookie names:** Old `gogeta_session_*` cookies ignored — users re-authenticate
- **Branch names:** Old `gogeta/gogeta-*` branches left in place, new ones use `gogeta/gogeta-*`

### Breaking Changes
- Package name change (`gogeta-agent` → `gogeta-agent`)
- CLI command changes (`gogeta` → `gogeta`)
- Config directory change (`~/.gogeta` → `~/.gogeta`)
- ENV var change (`GOGETA_HOME` → `GOGETA_HOME`)
- Cookie name changes (session invalidation)
