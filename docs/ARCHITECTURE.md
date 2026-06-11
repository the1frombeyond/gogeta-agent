# Gogeta / Gogeta Architecture

## Layer Model

The codebase is organized into strict layers numbered 0–9. Dependencies must flow **downward** (higher layers may import lower layers; lower layers must never import higher layers).

```
Layer 9 ─ Presentation / UI   (tui_gateway/, ui-tui/, apps/desktop/, website/)
    ↑
Layer 8 ─ CLI Application     (gogeta_cli/*)
    ↑
Layer 7 ─ Gateway             (gateway/*)
    ↑
Layer 6 ─ Cron                (cron/*)
    ↑
Layer 5 ─ Orchestration       (run_agent.py, cli.py, model_tools.py, batch_runner.py, toolsets.py, mcp_serve.py)
    ↑
Layer 4 ─ Agent Core          (agent/*)
    ↑
Layer 3 ─ Plugin System       (plugins/*, gogeta_cli/plugins.py, gogeta_cli/middleware.py)
    ↑
Layer 2 ─ Provider Registry   (providers/*, plugins/model-providers/*)
    ↑
Layer 1 ─ Tool Implementations (tools/*)
    ↑
Layer 0 ─ Foundation          (gogeta_constants.py, utils.py, gogeta_state.py, gogeta_logging.py, gogeta_time.py)
```

---

## Layer Definitions

### Layer 0: Foundation
**Files:** `gogeta_constants.py`, `utils.py`, `gogeta_state.py`, `gogeta_logging.py`, `gogeta_time.py`

**Allowed imports:** stdlib only, `python-dotenv`

**Rules:**
- No imports from any other layer or project module
- Must be pure utility code with no side effects at import time
- `gogeta_constants.py` is the most foundational — keeps `get_gogeta_home()`, profile-aware paths

### Layer 1: Tool Implementations
**Directories:** `tools/` (all `.py` files), `tools/environments/`, `tools/computer_use/`

**Allowed imports:** Layer 0, `tools.registry`, `tools.interrupt`, `tools.thread_context`, cross-tool helpers within `tools/`, stdlib

**Rules:**
- Each tool file self-registers via `registry.register()` at module level
- No imports from `agent/`, `gateway/`, `gogeta_cli/`, `plugins/`, `providers/`
- Terminal backends (`tools/environments/`) may import `tools.interrupt` only
- Schema descriptions must not hardcode cross-tool references from other toolsets

### Layer 2: Provider Registry
**Files:** `providers/__init__.py`, `providers/base.py`
**Directories:** `plugins/model-providers/*/`

**Allowed imports:** Layer 0, `providers.base`, `providers.__init__`, stdlib

**Rules:**
- Defines `ProviderProfile` ABC and `register_provider()` interface
- Model-provider plugins call `register_provider()` at module load
- No imports from `agent/`, `tools/`, `gateway/`, `gogeta_cli/`

### Layer 3: Plugin System
**Files:** `gogeta_cli/plugins.py`, `gogeta_cli/middleware.py`
**Directories:** `plugins/` (general plugins, memory/*, kanban/, platform adapters, etc.)

**Allowed imports:** Layer 0–2, `gogeta_cli.config`, `gogeta_cli.middleware`, stdlib

**Rules:**
- `PluginManager` discovers plugins from `~/.gogeta/plugins/` and bundled paths
- Plugins expose `register(ctx)` for hooks, tools, CLI subcommands
- Plugin code must NOT import `agent/`, `gateway/`, `run_agent.py`, `cli.py` directly
- Hook interfaces are the only communication channel between plugins and agent core

### Layer 4: Agent Core
**Directory:** `agent/` (all subdirectories: `transports/`, `lsp/`, `secret_sources/`, all `.py` files)

**Allowed imports:** Layers 0–3 (with lazy imports for Layer 3 to avoid circulars), `gogeta_state`, `model_tools` (lazy via forwarder)

**Rules:**
- Core conversation loop, memory management, context compression, tool dispatch
- May reference `gogeta_cli.plugins`, `gogeta_cli.middleware`, `gogeta_cli.config` only via **lazy imports** inside functions
- Must NOT import `gateway/`, `run_agent.py` (except via lazy forwarder), `cli.py`, `tui_gateway/`
- All provider interactions go through `agent/transports/` adapters

### Layer 5: Orchestration
**Files:** `run_agent.py`, `cli.py`, `model_tools.py`, `batch_runner.py`, `toolsets.py`, `mcp_serve.py`

**Allowed imports:** Layers 0–4, `gogeta_state`, `gogeta_cli.*`, `cron.*`

**Rules:**
- Thin wiring layer — combines agent, tools, plugins, and CLI into runnable surfaces
- `run_agent.py` defines `AIAgent` class consumed by gateway and CLI
- `model_tools.py` holds global tool state; must gate writes with save/restore around subagents
- `cli.py` is the interactive CLI orchestrator — owns prompt loop, display, slash command dispatch

### Layer 6: Cron
**Directory:** `cron/`

**Allowed imports:** Layers 0–5, `gogeta_cli.plugins`

**Rules:**
- Job store (`jobs.py`) + scheduler tick loop (`scheduler.py`)
- Cron sessions pass `skip_memory=True` by default
- 3-minute hard interrupt on cron sessions

### Layer 7: Gateway
**Directory:** `gateway/` (including `platforms/*`, `builtin_hooks/*`)

**Allowed imports:** Layers 0–6, `gogeta_cli.*` (config, plugins, commands, fallback_config, env_loader)

**Rules:**
- Must NOT import `tools/` directly — communicates through agent
- Platform adapters use token locks for profile isolation
- Two sequential message guards: base adapter queuing + runner command interception
- New commands that must reach the runner while agent is blocked must bypass both guards

### Layer 8: CLI Application
**Directory:** `gogeta_cli/` (all subdirectories: `proxy/`, `dashboard_auth/`)

**Allowed imports:** Layers 0–7

**Rules:**
- Argparse entry point in `main.py` wires all subcommands
- Config loading, skin engine, command registry, banner
- `commands.py` — central `COMMAND_REGISTRY` — sole source of truth for slash commands
- Must NOT import `tools/` directly (except `plugins.py` which does so for registration)

### Layer 9: Presentation / UI
**Directories:** `tui_gateway/`, `ui-tui/`, `apps/desktop/`, `website/`

**Allowed imports:** Layers 0–8 (tui_gateway constructs `AIAgent`)

**Rules:**
- TypeScript owns the screen; Python owns session/model/tool logic
- Never duplicate the transcript or composer in React — extend Ink instead
- Desktop app has its own curated slash-command palette

---

## Dependency Rules

### Strict Prohibition
The following imports are **never allowed**:

| Violation | Why |
|-----------|-----|
| Lower layer importing higher layer | Breaks the dependency direction — creates circular risk and coupling |
| `tools/*` importing `agent/*` | Tools must be standalone; agent code may use tools but tools may not depend on agent |
| `providers/*` importing `agent/*` or `gateway/*` | Providers define the interface, not the consumers |
| `gateway/*` importing `tools/*` directly | Gateway communicates through agent, never directly to tool implementations |
| `agent/*` importing `gateway/*` | Agent core must be platform-agnostic |
| Hardcoding `~/.gogeta` paths | Breaks profile isolation — use `get_gogeta_home()` from `gogeta_constants` |

### Allowed Cross-Layer Patterns

| Pattern | Example |
|---------|---------|
| Lazy import for plugins | `from gogeta_cli.plugins import ...` inside a function, not at module top level |
| Forwarder reference | `_ra()` in agent code to access `run_agent` symbol lazily |
| Registry pattern | Tools register themselves with `tools/registry.py`; agent discovers them through the registry (not direct import) |
| Plugin hooks | Plugin system provides lifecycle hooks; agent code calls `emit()` at appropriate points |
| ABC + discovery | `providers/base.py` defines ABC; consumers discover implementations through `get_provider_profile()` |

---

## File Size Budget

Hard target for Python files:

| Size | Classification | Action |
|------|----------------|--------|
| 0–300 lines | Ideal | No action needed |
| 300–800 lines | Acceptable | Prefer splitting when touching |
| 800–1000 lines | Warning | Split on next significant edit |
| 1000+ lines | Megafile | Must be split before any architectural change |

Current megafiles (1000+ lines): `gateway/run.py` (~18k), `cli.py` (~14.5k), `gogeta_cli/main.py` (~14k), `run_agent.py` (~12k), `gogeta_cli/web_server.py` (~5k), `tui_gateway/server.py` (~3k), `gogeta_cli/plugins.py` (~1.9k).

---

## Architectural Invariants

The following invariants are enforced by the architecture enforcer:

1. **Layer purity** — no file imports from a layer above its own
2. **No gateway→tools imports** — gateway must not import `tools/*` directly
3. **No agent→gateway imports** — agent core must not import `gateway/*`
4. **No tools→agent imports** — tools must not import `agent/*`
5. **No providers→agent imports** — provider registry must not import `agent/*`
6. **Foundation purity** — Layer 0 must not import any project module
7. **Lazy plugin imports** — agent code must import `gogeta_cli.plugins` lazily (inside functions)
8. **Profile-safe paths** — no hardcoded `~/.gogeta` paths (use `get_gogeta_home()`)
9. **Sole command registry** — all slash commands defined in `gogeta_cli/commands.py`
10. **Tool self-registration** — all tools call `registry.register()` at module level

## Identity Transformation

Throughout the migration from Gogeta → Gogeta, the following identity rules apply:

- **`pyproject.toml`** — name changes from `gogeta-agent` to `gogeta` at final release
- **Package names** — `gogeta_cli/` → `gogeta_cli/`, `gogeta_constants.py` → `gogeta_constants.py`, etc. (applied per-file as touched)
- **Config paths** — `~/.gogeta/` → `~/.gogeta/` (applied during profile-safe path migration)
- **Script entry points** — `gogeta`, `gogeta-agent`, `gogeta-acp` → `gogeta`, `gogeta-agent`, `gogeta-acp`
- **Environment variables** — `GOGETA_HOME` → `GOGETA_HOME`, `GOGETA_TUI` → `GOGETA_TUI`, etc.
- **Gogeta-native assets** (`lifeline/`, `skills/`, `tui/`, `tools/`) are preserved and integrated — never replaced
