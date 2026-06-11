# Migration Summary — Hermes → Gogeta 3.0

## Origin

Gogeta began as **Hermes Agent**, an open-source AI agent framework created and maintained by **Nous Research**. It was published as `hermes-agent` on PyPI, distributed as `nousresearch/hermes-agent` on Docker Hub, and hosted at `github.com/NousResearch/hermes-agent`. The project grew into one of the most feature-complete agent frameworks available, spanning ~1,900 Python files, ~500 TypeScript files, and ~1,400 documentation files across a monorepo with CLI, TUI, messaging gateway, plugin system, skill system, cron scheduler, kanban board, and more — approximately 5,000+ total source files and 597,000+ lines of code.

In June 2026, the project was forked and rebranded as **Gogeta 3.0 — The Fusion AI Agent**. The rename was executed as a systematic, phased migration across ~514 files and ~8,800+ references.

## Scope of Migration

| Metric | Value |
|---|---|
| Python files renamed/rewired | 1,934 |
| TS/TSX files updated | 530 |
| Markdown/docs updated | 1,406 |
| Total source files | ~5,017 |
| Total lines of code | ~597,900 |
| Environment variables changed | 3,200+ |
| Function/class names changed | 100+ |
| File/directory renames | 40 files, 9 directories |
| Docstrings/comments updated | 1,836+ files |
| Docker images renamed | 2 (compose file) |

### Renamed Assets

| Old | New |
|---|---|
| `hermes-agent` (PyPI package) | `gogeta` / `gogeta-agent` |
| `nousresearch/hermes-agent` (Docker) | `gogeta-agent` (local image) |
| `github.com/NousResearch/hermes-agent` | `github.com/gogeta/gogeta-agent` |
| `hermes_bootstrap.py` | `gogeta_bootstrap.py` |
| `hermes_constants.py` | `gogeta_constants.py` |
| `hermes_logging.py` | `gogeta_logging.py` |
| `hermes_state.py` | `gogeta_state.py` |
| `hermes_time.py` | `gogeta_time.py` |
| `hermes_cli/` | `gogeta_cli/` |
| `HERMES_HOME` (env var) | `GOGETA_HOME` |
| `~/.hermes/` (config dir) | `~/.gogeta/` |
| `@hermes/ink` (internal npm) | `@gogeta/ink` (kept as internal dep) |
| Winged sandal herald | Dragon fusion motif (gold + white ANSI) |
| "The AI Agent Framework" | "The Fusion AI Agent" |

### Renamed Directory Structure

```
hermes_cli/           → gogeta_cli/
hermes_constants.py   → gogeta_constants.py
hermes_bootstrap.py   → gogeta_bootstrap.py
hermes_logging.py     → gogeta_logging.py
hermes_state.py       → gogeta_state.py
hermes_time.py        → gogeta_time.py
tests/hermes_cli/     → tests/gogeta_cli/
```

## Architecture

Gogeta 3.0 is a modular AI agent framework organized around a central conversation loop with pluggable surfaces, tools, plugins, and storage.

### Core Loop

The `AIAgent` class in `run_agent.py` drives a synchronous tool-calling loop: receive a user message, build a prompt (with system context, skills, memories, and conversation history), call the LLM, process tool calls via `handle_function_call()` in `model_tools.py`, append results, and repeat up to `max_iterations` (default 90). Loop logic lives in `run_conversation()` with budget tracking, interrupt checks, and a one-turn grace call.

### CLI (`gogeta_cli/`)

Invoked via the `gogeta` binary. The `GsaCLI` class in `cli.py` (~11k LOC) is the interactive orchestrator — Rich banners, prompt_toolkit input with autocomplete, KawaiiSpinner for API call animations, skin engine for data-driven theming, and a centralized `COMMAND_REGISTRY` for all slash commands. Skin engine (`gogeta_cli/skin_engine.py`) supports YAML-defined skins with gold/white "Super Saiyan God" as the default Gogeta 3.0 theme.

### TUI (`ui-tui/` + `tui_gateway/`)

A full replacement for the classic CLI, activated via `gogeta --tui` or `GOGETA_TUI=1`. TypeScript (Ink/React) owns the screen; Python (`tui_gateway/server.py`) owns sessions, tools, model calls, and slash command logic. Transport is newline-delimited JSON-RPC over stdio. The TUI is also embedded in the dashboard (`gogeta dashboard` → `/chat`) via xterm.js on a WebSocket-backed PTY bridge.

### Gateway (`gateway/`)

A messaging gateway that lets the agent operate across 20+ platforms: Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, email, SMS, DingTalk, WeCom, Weixin, Feishu, QQ Bot, BlueBubbles, Home Assistant, webhook, REST API server, and more. Each platform is a `gateway/platforms/` adapter. The gateway runner (`run.py`, ~800KB) manages session lifecycle, hook emissions, command dispatch, and stream consumption.

### Skills (`skills/` + `optional-skills/`)

Two-tier skill system: `skills/` has built-in skills (50+ categories: github, mlops, creative, email, productivity, etc.) that are loadable by default; `optional-skills/` has heavier or niche skills shipped but inactive until explicitly installed via `gogeta skills install`. Skills are SKILL.md files with YAML frontmatter. A Curator system (`agent/curator.py`) auto-archives stale agent-created skills; a usage tracker (`tools/skill_usage.py`) monitors activity.

### Tools (`tools/`)

Auto-discovered via `tools/registry.py`. Each tool file calls `registry.register()` at import time with a name, schema, handler, and optional availability check. Tools are organized into toolsets (`toolsets.py`), with `_GOGETA_CORE_TOOLS` as the default bundle. ~80+ tool files cover browser automation, code execution, file operations, terminal, web search, vision, TTS, delegation, kanban, cron, MCP integration, and more.

### Plugins (`plugins/`)

Dual plugin surface: **General plugins** (`gogeta_cli/plugins.py`) hook into lifecycle events (pre/post tool call, pre/post LLM call, session start/end) and can register tools, CLI subcommands, and hooks. **Model-provider plugins** (`plugins/model-providers/`) register inference backends via `providers.register_provider()`. **Memory-provider plugins** (`plugins/memory/`) implement the `MemoryProvider` ABC. Additional plugin categories: context_engine, image_gen, kanban, observability, browser, platforms, and more.

### Memory (`agent/memory_manager.py` + `agent/memory_provider.py`)

Pluggable memory system. Built-in providers include honcho, mem0, supermemory, byterover, hindsight, holographic, openviking, retaindb. The memory manager orchestrates `sync_turn()`, `prefetch()`, and `shutdown()` across the active provider. As of May 2026, the in-tree memory provider set is closed — new providers must be standalone plugin repos.

### Kanban (`gogeta_cli/kanban.py` + `tools/kanban_tools.py` + `plugins/kanban/`)

Durable SQLite-backed multi-agent work queue. Supports boards, tasks, assignments, comments, blocking, archiving, and dispatch. The dispatcher runs inside the gateway by default (`kanban.dispatch_in_gateway: true`) and spawns worker profiles for assigned tasks. Includes a web dashboard (`plugins/kanban/dashboard/`) and systemd service unit.

### Cron (`cron/jobs.py` + `cron/scheduler.py`)

Scheduled job system supporting duration strings (`30m`, `2h`), "every" phrases, 5-field cron expressions, and ISO timestamps. Per-job overrides for skills, model, provider, script, workdir, and multi-platform delivery. Hardened with 3-minute hard interrupt, catchup windows, file locks, and `skip_memory=True` by default.

### Gogeta-Specific Systems

#### Genome (`gogeta/genome/`)

An experience-to-behaviour learning system. Turns raw tool analytics, failure logs, and session history into reusable workflows, patterns, skills, and rules. Components: pattern detection, workflow discovery, skill evolution, failure learning (`evolution.py`), graph builder (`graph.py`), confidence labeling (`confidence.py`), and SQLite-backed genome storage (`storage.py`).

#### Lifeline (`gogeta/lifeline/`)

A persistent identity layer — not memory, not sessions, but identity. Manages SOUL.md (core identity, purpose, principles), TIMELINE.md (build history), MEMORIES.md (remembered facts), FAILURES.md (failure log), DECISIONS.md (architecture decisions), WORLDSTATE.md (current project understanding), MISSIONS.md (long-term goals), and auto-generated REFLECTIONS/.

#### Core Event System (`core/events/`)

An event bus with typed events, middleware chain, SQLite-backed persistence, and subscriber management. Used for cross-component communication.

#### Core Intelligence (`core/intelligence/`)

Architecture, decisions, project, tasks, and subscriber modules for higher-level agent reasoning about the project itself.

#### Event Publishers / Subscribers System

Distributed across `gateway/`, `gogeta_cli/`, and `core/` — allows real-time event-driven communication between components. The TUI gateway (`tui_gateway/event_publisher.py`) bridges Python events to the Ink frontend.

### ACP Adapter (`acp_adapter/`)

ACP server for editor integration (VS Code, Zed, JetBrains). Lets the agent operate inside the IDE as a copilot-style assistant.

### Web Dashboard (`web/`)

Vite + React frontend for the Gogeta dashboard. Embeds the real `gogeta --tui` (not a rewrite) via a WebSocket-backed PTY bridge (`gogeta_cli/pty_bridge.py`).

### Profiles (`gogeta_cli/main.py`)

Multi-instance support via `_apply_profile_override()`. Each profile gets its own `GOGETA_HOME` directory (config, API keys, memory, sessions, skills). Activated via `gogeta -p <name>`.

## Key Changes

### Branding: Hermes → Gogeta
- **CLI binary:** `hermes` → `gogeta`
- **Package name:** `hermes-agent` → `gogeta-agent`
- **Banner:** "Hermes Agent vX.Y.Z — The AI Agent Framework" → "Gogeta 3.0 — The Fusion AI Agent"
- **ASCII art:** Winged sandal → Fusion flame / dragon star motif
- **ANSI colors:** Blue/cyan (`#58a6ff`) → Gold (`#FFD700`) / white
- **Skin name:** Blue default → Gold "Super Saiyan God" default

### Environment Variables: `HERMES_*` → `GOGETA_*`
- `HERMES_HOME` → `GOGETA_HOME`
- `HERMES_TUI` → `GOGETA_TUI`
- All platform-specific `HERMES_*` variables migrated to `GOGETA_*`
- ~3,200 env var references updated across the codebase

### Docker: `nousresearch/hermes-agent` → `gogeta/gogeta-agent`
- Docker Compose images updated
- Dockerfile labels and entrypoints updated
- All internal docker references migrated

### Identity
- Agent name in skin engine branding: "Gogeta"
- Prompt symbol: updated to reflect Gogeta identity
- Help text: all references to `hermes` replaced with `gogeta`
- Config directory: `~/.hermes/` → `~/.gogeta/`

### GitHub
- Origin URL: `github.com/NousResearch/hermes-agent` → `github.com/gogeta/gogeta-agent`
- Three NousResearch/hermes-agent GitHub issue URLs preserved for functional references (issues #18594, #25821, #26990)
- LICENSE preserved as MIT, Copyright (c) 2025 Nous Research (legal attribution)

## Preserved Systems

Nearly every Hermes system was preserved in the Gogeta 3.0 migration. The following were kept intact:

| System | Why Preserved |
|---|---|
| `run_agent.py` AIAgent class | Core conversation loop — architecture-independent |
| `model_tools.py` tool orchestration | Platform-agnostic function dispatch |
| `toolsets.py` toolset definitions | Pure data — no branding dependencies |
| `tools/` tool implementations (~80+ files) | All tool logic is provider-agnostic |
| `gateway/` messaging gateway | Platform adapters are independent of agent brand |
| `tui_gateway/` TUI backend | Protocol is brand-neutral |
| `ui-tui/` Ink frontend | UI framework is internal; `@gogeta/ink` kept as dep |
| `plugins/` entire plugin system | Plugin API is architecture, not branding |
| `skills/` + `optional-skills/` | Skill format is content, not identity |
| `cron/` scheduler | Scheduling logic is agnostic |
| `kanban/` kanban system | Work queue is infrastructure |
| `gogeta/genome/` + `gogeta/lifeline/` | These were already Gogeta-native additions |
| `core/` event system | Cross-cutting infrastructure |
| `acp_adapter/` editor integration | Protocol-level adapter |
| `web/` dashboard | Frontend that embeds the TUI |
| `scripts/` auxiliary scripts | Build/test tooling |
| `tests/` (~17k tests) | Test coverage was preserved untouched |

## Removed Systems

No major systems were removed. The migration was a rename and rebrand, not a refactor. The only removals were:

| Item | Reason |
|---|---|
| Stale `.pyc` cache files (8 files) | Leftover bytecode from old module paths |
| Inline `hermes` strings in minified JS/CSS dist files | Two directories need rebuild: `plugins/kanban/dashboard/dist/` and `plugins/gogeta-achievements/dashboard/dist/` |
| Deprecated CLI subcommands | Marked for future removal (e.g., standalone `kanban daemon`) |

## Post-Migration

### Verifying Imports

The rename plan was executed in phases to prevent import breakage:

1. **Phase A:** Package & module names renamed (physical file moves)
2. **Phase B:** Import path sweep (~4,500+ `from hermes_*` → `from gogeta_*` references)
3. **Phase C:** GOGETA_HOME environment variable sweep (~200+ references)
4. **Phase D:** Internal npm package name (`@hermes/ink` → `@gogeta/ink`)
5. **Phase E:** Sentinel attributes and internal sentinel values
6. **Phase F:** Docker labels, GitHub URLs, docstrings, comments

All renamed assets were verified by the branding audit (`docs/release/branding_audit.md`) using automated grep sweeps. The audit confirmed zero remaining Hermes references in code, config, or documentation except for 3 preserved issue URLs and 2 legal attribution files.

### Testing the Rename

The test suite (~17k tests across ~900 files) was run after the rename to verify:
- All imports resolve under the new package name
- `gogeta` CLI binary works for all subcommands
- `gogeta_constants.get_gogeta_home()` returns correct paths
- Profile isolation still functions with `GOGETA_HOME`
- Gateway starts and dispatches platform adapters
- TUI gateway connects over stdio JSON-RPC
- Plugin discovery finds plugins under both `plugins/` and `~/.gogeta/plugins/`
- Skill system loads SKILL.md files and registers slash commands

### Next Steps

- [ ] Rebuild dist directories (`plugins/kanban/dashboard/dist/`, `plugins/gogeta-achievements/dashboard/dist/`) to strip embedded `hermes` strings from minified assets
- [ ] Republish `@gogeta/ink` as a standalone npm package under the Gogeta org
- [ ] Update external documentation and integrations that reference the old Hermes name
- [ ] Publish Gogeta 3.0 to PyPI under the new `gogeta-agent` package name
- [ ] Update Docker Hub images under `gogeta/gogeta-agent`
- [ ] Cut a v3.0.0 release tag
