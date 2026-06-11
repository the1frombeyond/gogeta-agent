# Gogeta Architecture

## Overview

Gogeta 3.0 is a modular AI agent framework organized around a core synchronous conversation loop (`run_agent.py`, ~5.3k LOC) that drives tool-calling LLMs. A thin orchestration layer (`model_tools.py`, ~1.2k LOC) bridges the loop to ~100+ self-registering tool modules (discovered via `tools/registry.py`). The agent can be accessed through three primary surfaces: a prompt_toolkit/Rich interactive CLI (`cli.py`, ~16k LOC), an Ink (React) terminal UI (`ui-tui/` + `tui_gateway/`), or a multi-platform messaging gateway (`gateway/`) supporting 20+ chat platforms. A plugin system, memory provider abstraction, scheduled cron system, skill framework, event bus, and Gogeta-specific identity/learning systems (Genome, Lifeline) complete the architecture. Configuration is profile-aware (`GOGETA_HOME`) supporting fully isolated multi-instance deployments.

---

## Core Components

### AIAgent (`run_agent.py`)

The central agent loop in `AIAgent.run_conversation()` is synchronous, with interrupt checks, iteration budget tracking, and a one-turn grace call:

```
while (api_call_count < max_iterations and iteration_budget.remaining > 0) or budget_grace_call:
    if interrupt_requested: break
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls: handle each → append result → continue
    else: return response.content
```

`AIAgent.__init__` accepts ~60 parameters (credentials, routing, callbacks, session context, budget, credential pool, provider, model, enabled/disabled toolsets, platform, session_id, skip_memory, skip_context_files, prefill_messages, service_tier, reasoning_config, etc.). Messages follow OpenAI format with reasoning stored in `assistant_msg["reasoning"]`. The `chat()` method provides a simple string-in/string-out interface; `run_conversation()` returns a dict with `final_response` + full `messages`.

The agent imports the OpenAI SDK via a lazy proxy (`agent/process_bootstrap.py`) that defers the ~240ms import until first use.

### CLI (`cli.py` + `gogeta_cli/`)

**`cli.py`** (`GsaCLI` class, ~16k LOC) uses **Rich** for banners/panels and **prompt_toolkit** for a fixed input-area REPL with autocomplete, history, and key bindings. `KawaiiSpinner` (`agent/display.py`) shows animated faces during API calls. `process_command()` dispatches slash commands via `resolve_command()` from the central `COMMAND_REGISTRY`.

**`gogeta_cli/main.py`** (~23k LOC) is the main entry point with all subcommand wiring (`chat`, `gateway`, `setup`, `cron`, `doctor`, `kanban`, `honcho`, `model`, `profile`, `tools`, `skills`, `logs`, `backup`, etc.). Profiles are applied via `_apply_profile_override()` before any imports. Config is loaded through three paths: `load_cli_config()` (CLI mode), `load_config()` (subcommands), or direct YAML load (gateway).

**`gogeta_cli/commands.py`** defines `COMMAND_REGISTRY` — a single list of `CommandDef` objects that feeds CLI dispatch, gateway help, Telegram menu, Slack mapping, autocomplete, and help categories.

**`gogeta_cli/commands.py`** → `COMMAND_REGISTRY`, **`gogeta_cli/plugins.py`** → `PluginManager`, **`gogeta_cli/skin_engine.py`** → data-driven skin system with 4 built-in skins, **`gogeta_cli/config.py`** → config defaults + `.env` metadata, **`gogeta_cli/banner.py`** → Rich banner rendering.

### TUI (`ui-tui/` + `tui_gateway/`)

Activated via `gogeta --tui`. A Node.js Ink (React) process communicates with a Python `tui_gateway` over newline-delimited JSON-RPC on stdio:

```
gogeta --tui
  └─ Node (Ink)  ──stdio JSON-RPC──  Python (tui_gateway/server.py, ~17k LOC)
       │                                  └─ AIAgent + tools + sessions
       └─ renders transcript, composer, prompts, activity
```

Key surfaces: chat streaming (`message.delta/complete`), tool activity (`tool.start/progress/complete`), approvals (`approval.request/respond`), session picker (`session.list/resume`), slash commands (local + `slash.exec` → `command.dispatch`), completions (`complete.slash`, `complete.path`). The dashboard (`gogeta dashboard` → `/chat`) embeds the real `gogeta --tui` via PTY bridge (`gogeta_cli/pty_bridge.py`) — never a rewrite.

A separate Electron desktop chat app (`apps/desktop/`) talks to `tui_gateway` over JSON-RPC with its own composer, transcript, and curated slash-command palette.

### Gateway (`gateway/`)

The messaging gateway (`gateway/run.py`, ~16k LOC + `gateway/platforms/`) provides platform adapters for messaging platforms. Each adapter extends `BaseAdapter` (`gateway/platforms/base.py`) and implements `connect()`, `disconnect()`, message handling, and optional long-polling/event-driven loops. Platforms include:

- **Built-in** (`gateway/platforms/`): telegram, discord, slack, whatsapp, signal, matrix, mattermost, email, sms, dingtalk, wecom, weixin, feishu, qqbot, bluebubbles, yuanbao, webhook, api_server (33 files)
- **Plugin-based** (`plugins/platforms/`): google_chat, homeassistant, irc, line, mattermost, ntfy, simplex, teams

`GatewayRunner` manages lifecycle: `start_gateway()` launches all configured platform adapters. Mixins in `gateway/watchers/` handle kanban dispatch, session lifecycle, process watchers, and platform reconnect.

### Model Providers (`plugins/model-providers/`)

29 model-provider plugin directories, each calling `providers.register_provider(ProviderProfile(...))` at module load. Scan order: bundled plugins → user plugins → legacy `providers/` dir. Lazy discovery via `providers/__init__.py._discover_providers()` — NOT through the general PluginManager.

Includes: openrouter, anthropic, gmi, deepseek, nvidia, gemini, openai-codex, bedrock, azure-foundry, ollama-cloud, huggingface, xai, minimax, copilot, copilot-acp, custom, arcee, nous, kilocode, kimi-coding, novita, stepfun, alibaba, alibaba-coding-plan, xiaomi, zai, qwen-oauth, opencode-zen. Each can be overridden by user-installed plugins (last-writer-wins).

### Tool System (`tools/` + `model_tools.py` + `toolsets.py`)

**`tools/registry.py`** (593 LOC) — the foundation. No imports from `model_tools` or tool files. `registry.register()` is called at module level by each tool file to declare schema, handler, toolset membership, and availability check. `discover_builtin_tools()` uses AST analysis to find `registry.register()` calls in `tools/*.py`.

**`model_tools.py`** (1.2k LOC) — thin orchestration. Triggers `discover_builtin_tools()`, collects schemas, routes `handle_function_call()` to the correct handler via the registry. Provides async→sync bridging via persistent per-thread event loops (prevents "Event loop is closed" errors with cached httpx clients).

**`toolsets.py`** (894 LOC) — `TOOLSETS` dict maps platform names to tool bundles. `_GOGETA_CORE_TOOLS` is the base set most platforms inherit from. Current toolset keys: browser, clarify, code_execution, cronjob, debugging, delegation, discord, discord_admin, feishu_doc, feishu_drive, file, homeassistant, image_gen, kanban, memory, messaging, moa, rl, safe, search, session_search, skills, spotify, terminal, todo, tts, video, vision, web, yuanbao.

**`tools/environments/`** — terminal backends: local, docker, ssh, modal, managed_modal, daytona, singularity.

**File dependency chain:**
```
tools/registry.py  (no deps)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

### Skill System (`skills/` + `tools/skills_tool.py`)

Two parallel surfaces: **`skills/`** (built-in skills, organized by category — github, mlops, creative, etc.) and **`optional-skills/`** (heavier/niche skills not active by default). Skill slash commands are injected as user messages (not system prompts) to preserve prompt caching. Curator (`agent/curator.py`) tracks usage on agent-created skills and auto-archives stale ones; never deletes.

### Plugin System (`plugins/` + `gogeta_cli/plugins.py`)

`PluginManager` discovers plugins from `~/.gogeta/plugins/`, `./.gogeta/plugins/`, and pip entry points. Each plugin exposes `register(ctx)` enabling:
- Lifecycle hooks: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`
- Tool registration via `ctx.register_tool()`
- CLI subcommand registration via `ctx.register_cli_command()`

Plugins MUST NOT modify core files. Discovery runs as a side effect of importing `model_tools.py`. Model-provider plugins have a separate discovery system in `providers/__init__.py`.

### Memory System (`agent/memory*.py` + `plugins/memory/`)

`MemoryProvider` ABC (in `agent/memory_provider.py`) orchestrated by `agent/memory_manager.py`. Lifecycle hooks: `sync_turn()`, `prefetch()`, `shutdown()`, `post_setup()`. Built-in memory plugins (8): honcho, mem0, supermemory, byterover, hindsight, holographic, openviking, retaindb. New backends must ship as standalone repos (policy, May 2026).

### Kanban (`plugins/kanban/`)

SQLite-backed multi-agent work queue with a dispatcher loop. CLI commands via `gogeta_cli/kanban.py`, worker toolset via `tools/kanban_tools.py`. Board-level isolation with tenant namespacing, stale-claim recovery, failure-limit auto-blocking, and dashboard web UI. Dispatcher runs inside the gateway by default.

### Cron (`cron/`)

`cron/jobs.py` (job store) + `cron/scheduler.py` (tick loop). Formats: duration ("30m"), "every" phrase ("every 2h"), cron expression ("0 9 * * *"), ISO timestamp. 3-minute hard interrupt on cron sessions. Catchup window, grace window, file lock prevents duplicate ticks. Cron sessions pass `skip_memory=True` by default.

### Session State (`gogeta_state.py`, ~8.7k LOC)

SQLite session store with FTS5 full-text search replacing per-session JSONL files. WAL mode for concurrent readers + one writer. Compression-triggered session splitting via `parent_session_id` chains. Session source tagging (`cli`, `telegram`, `discord`, etc.).

---

## Data Flow

### User Input → AIAgent Loop

```
User Input → CLI/Gateway/TUI
  → run_agent.py: run_conversation(message)
    → prompt_builder.py: build system prompt + skill prompts + context files
    → agent/memory_manager.py: sanitize_context()
    → model_tools.py: get_tool_definitions(enabled_toolsets, disabled_toolsets)
      → tools/registry.py: collect schemas from registered tools
    → API call (OpenAI-compatible): chat.completions.create(messages + tools)
    → If tool_calls:
        → model_tools.py: handle_function_call(name, args)
          → tools/registry.py: dispatch to registered handler
          → Plugin hooks: pre_tool_call / post_tool_call
        → Append tool result → loop
    → Else: return final response
```

### Tool Call Flow

```
handle_function_call(name, args, task_id)
  → pre_tool_call plugin hooks
  → registry.dispatch(name, args, task_id, user_task)
    → handler(args, task_id=task_id)
    → handler returns JSON string
  → post_tool_call plugin hooks
  → tool_result is appended to messages
```

### Plugin Hook Lifecycle

```
session_start → on_session_start hooks
  turn_start → pre_llm_call hooks
    tool_call → pre_tool_call hooks → handler → post_tool_call hooks
  turn_end → post_llm_call hooks
session_end → on_session_end hooks
```

---

## Configuration

### Config System

Three config loaders:
| Loader | Used by | Location |
|--------|---------|----------|
| `load_cli_config()` | CLI mode | `cli.py` |
| `load_config()` | Subcommands | `gogeta_cli/config.py` |
| Direct YAML | Gateway | `gateway/run.py` + `gateway/config.py` |

Top-level `config.yaml` sections (non-exhaustive): `model`, `agent`, `terminal`, `compression`, `display`, `stt`, `tts`, `memory`, `security`, `delegation`, `smart_model_routing`, `checkpoints`, `auxiliary`, `curator`, `skills`, `gateway`, `logging`, `cron`, `profiles`, `plugins`, `honcho`.

Secrets go in `.env` (API keys only), not `config.yaml`. Non-secret settings belong in `config.yaml`.

### Profile System

`_apply_profile_override()` in `gogeta_cli/main.py` sets `GOGETA_HOME` before module imports. All code must use `get_gogeta_home()` (from `gogeta_constants`) for paths. `display_gogeta_home()` for user-facing messages. Each profile has fully isolated config, API keys, memory, sessions, skills, and gateway state. Profiles root at `~/.gogeta/profiles/`.

---

## Container/Docker Architecture

`docker-compose.yml` + `docker-compose.windows.yml` with `Dockerfile`. Uses s6-overlay for process supervision (`docker/s6-rc.d/`). Contains entrypoint script, gogeta-exec shim, stage2 hook, and a SOUL.md. Nix flake (`flake.nix` + `flake.lock`) for Nix-based deployments.

---

## Gogeta-Specific Systems

### Genome (`gogeta/genome/`)

Experience-to-behavior learning system. `GenomeManager` (`genome.py`) orchestrates:

- **`workflows.py`** — Discovers multi-step workflows from tool transition frequencies in the analytics store. Builds directed graphs, walks most-probable paths, deduplicates chains.
- **`patterns.py`** — N-gram pattern detection (2–5 tool sequences) over recent tool call history. Scores with confidence.
- **`skills.py`** — Merges high-confidence workflows + patterns into skill definitions stored in `genome.json`.
- **`evolution.py`** — Parses `FAILURES.md` entries and extracts reusable rules that prevent repeat mistakes.
- **`confidence.py`** — Thresholds: <0.30 seed, 0.30–0.60 emerging, 0.60–0.85 verified, >0.85 trusted/promoted.
- **`graph.py`** — Builds D3-friendly `workflow_graph.json` for visualization.
- **`storage.py`** — JSON + SQLite dual storage for `genome.json` (human-readable) and `genome.db` (graph queries).

### Lifeline (`gogeta/lifeline/`)

Persistent identity and memory files managed by `LifelineManager` (`lifeline.py`). All files live under `gogeta/lifeline/`:

- `SOUL.md` — Core identity and agent description
- `TIMELINE.md` — Chronological log of key events and milestones
- `MEMORIES.md` — Persistent long-term memories
- `FAILURES.md` — Recorded failures for genome learning
- `IDENTITY.md`, `ENERGY.md`, `RITUALS.md`, `TASTES.md`, `WORLDSTATE.md`, `USER.md`, `SYSTEM_RULES.md`, `LEGACY.md`
- `REFLECTIONS/` — Periodic reflection documents
- `DREAMS/`, `JOURNAL/`, `THOUGHTS/`, `MISSIONS/`, `SKILLS/` — Sub-directories for structured introspection

### Hierarchy (`gogeta/hierarchy/`)

[Explored as empty/general directory — reserved for agent role/authority hierarchy system]

### Core Event Bus (`core/events/`)

`EventBus` — synchronous in-process pub/sub with typed events (`EventType` enum: `tool.started`, `tool.finished`, `tool.failed`, `session.started`, `session.ended`, `provider.requested`, `provider.completed`, `provider.failed`, `provider.fallback`, `message.received`, `message.sent`, `agent.created`, `agent.destroyed`, `subagent.*`, `skill.*`). Thread-safe, priority-ordered subscribers, middleware pipeline, history buffer (configurable max 1000 events).

### Intelligence (`core/intelligence/`)

Subscriber-based intelligence system: `architecture.py`, `decisions.py`, `project.py`, `tasks.py`. Listens on the event bus and maintains higher-level context (architectural decisions, project state, task tracking).

### ACP Adapter (`acp_adapter/`)

Agent Communication Protocol server for VS Code / Zed / JetBrains IDE integration. Contains `server.py`, `session.py`, `tools.py`, `auth.py`, `events.py`, `permissions.py`, `edit_approval.py`.

### Lifeline (top-level `lifeline/`)

Repository-level identity system with the same file structure as `gogeta/lifeline/` — `SOUL.md`, `IDENTITY.md`, `FAILURES.md`, `MEMORIES.md`, `TIMELINE.md`, plus `DREAMS/`, `JOURNAL/`, `THOUGHTS/`, `MISSIONS/`, `SKILLS/`, `REFLECTIONS/`.

---

## Key Design Decisions

1. **Synchronous agent loop** — `run_conversation()` is entirely synchronous with iteration budget + interrupt checks. No asyncio in the core loop. Async is bridged only for tool handlers via persistent per-thread event loops.

2. **Self-registering tools** — Each `tools/*.py` calls `registry.register()` at import time. AST analysis discovers which modules to import. No manual import list to maintain — but wiring into a toolset in `toolsets.py` is still a deliberate manual step.

3. **OpenAI-format messages throughout** — The agent loop, memory system, and context compression all use a single message format (`{"role": "system/user/assistant/tool", ...}`). Reasoning stored in `assistant_msg["reasoning"]`.

4. **Profile isolation** — `GOGETA_HOME` env var scopes all state. Hardcoding `~/.gogeta` breaks profiles. Every path reference must use `get_gogeta_home()`.

5. **Prompt caching must not break** — System prompt mutations (skills, tools, memory) are cache-aware: deferred by default, opt-in `--now` for immediate invalidation. No mid-conversation context mutation.

6. **Plugin surfaces over core patches** — Plugins register hooks, tools, and CLI commands without touching core files. Policy: plugins MUST NOT modify `run_agent.py`, `cli.py`, `gateway/run.py`, or `gogeta_cli/main.py`.

7. **Two message guards in gateway** — Incoming messages during an active session are queued by the base adapter, then the gateway runner intercepts control commands (`/stop`, `/new`, `/approve`, `/deny`) before they reach `running_agent.interrupt()`.

8. **Subprocess-per-test isolation** — Each test runs in a freshly spawned Python subprocess (`multiprocessing.get_context("spawn")`). Module-level dicts/sets and ContextVars cannot leak. ~0.5–1.0s overhead per test, amortized by xdist.

9. **Genome as meta-learning** — The genome system learns from tool call history (pattern detection, workflow discovery, failure analysis) and promotes high-confidence patterns into skills — a feedback loop that makes the agent improve over time.

10. **Gateway as universal adapter** — 20+ messaging platforms share a single `GatewayRunner` via platform adapters. The `COMMAND_REGISTRY` in `gogeta_cli/commands.py` feeds CLI, gateway, Telegram menu, Slack mapping, and autocomplete from one source of truth.
