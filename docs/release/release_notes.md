# Gogeta 3.0 Release Notes

## What Was Inherited from Hermes

Gogeta began as a fork of the Hermes agent framework. From that foundation we inherited:

- **Core agent loop** — the `AIAgent` conversation loop with tool calling, iteration budgeting, and interrupt handling
- **Tool registry** — the `tools/registry.py` auto-discovery system for registering and dispatching tools
- **Provider architecture** — modular provider adapters for LLM backends (OpenAI, Anthropic, etc.)
- **Gateway system** — multi-platform messaging gateway supporting Telegram, Discord, Slack, and 20+ other platforms
- **Plugin framework** — `PluginManager` with lifecycle hooks and tool registration

## What Was Rebuilt

- **CLI architecture** — completely rewritten `cli.py` with a modular command registry, skin engine, and curses-based interactive menus
- **Session management** — `SessionDB` with SQLite-backed FTS5 search, profile-aware storage, and session recaps
- **Config system** — unified `DEFAULT_CONFIG` deep-merge loader with profile support and env-var bridging
- **Skill system** — `skill_commands.py` with slash-command injection, `skills_hub.py` for optional skills, and curator auto-maintenance

## What Is Uniquely Gogeta

- **Skin engine** (`gogeta_cli/skin_engine.py`) — data-driven CLI theming with 4 built-in skins (default, ares, mono, slate) and user-installable YAML skins
- **TUI** — full Ink (React) terminal UI with JSON-RPC backend, streaming chat, session picker, and completions
- **Cron scheduler** — `cron/jobs.py` + `cron/scheduler.py` with 4 schedule formats, 3-minute hard interrupt, and multi-platform delivery
- **Kanban system** — durable SQLite-backed multi-agent work queue with dispatcher, dashboard, and systemd integration
- **Profiles** — fully isolated multi-instance support with per-profile `GOGETA_HOME`, credential locks, and independent skill/config state
- **Curator** — background skill lifecycle management: tracks usage, auto-archives stale skills, never deletes, respects pinned skills
- **ACP adapter** — Agent Communication Protocol server for VS Code / Zed / JetBrains integration
- **Lifeline** — continuous agent loop with quality gates, evals, and recovery controls
- **Genome** — self-improving agent that evolves skills from experience
- **Marketplace** — skill distribution through the Skills Hub with GitHub App JWT auth
- **Web dashboard** — localhost SPA with embedded TUI via PTY bridge, sidebar widgets, and model/theme controls
- **Desktop app** — Electron chat app with its own renderer and curated slash-command surface

## New Architecture

```
gogeta [--tui]
  └─ CLI (prompt_toolkit)  OR  TUI (Ink via JSON-RPC)  OR  Gateway (any platform)
       │                            │                              │
       └──── AIAgent (run_agent.py) ◄─────────────── plugins ──────┘
                      │
          ┌───────────┼───────────┬─────────────────┐
          │           │           │                 │
      tools/    gateway/      cron/            acp_adapter/
   (registry)  (platforms)  (scheduler)     (protocol)
```

## New Capabilities

- One-command installation via `curl -fsSL URL | bash`
- Zero-config first-run experience with setup wizard
- `gogeta doctor` — diagnostic tool that validates config, API keys, and environment
- `gogeta logs --follow` — real-time log streaming with level filtering
- `gogeta cron` — full cron job lifecycle (add, edit, pause, resume, run, remove)
- `gogeta kanban` — multi-agent work queue with dispatch daemon
- `gogeta curator` — skill lifecycle management (status, run, pause, archive, restore, backup)
- `gogeta profile` — multi-instance profile management
- `gogeta skin` — live theme switching at runtime
- `gogeta tools` — curses-based toolset configuration
- TUI with streaming chat, session picker, and slash completions

## Migration Notes

### From Hermes 2.x

1. Install Gogeta fresh — no migration script is provided for Hermes config
2. Transfer API keys manually from `~/.hermes/.env` to `~/.gogeta/.env`
3. Transfer custom skills from `~/.hermes/skills/` to `~/.gogeta/skills/`
4. Plugin API is **not compatible** — Gogeta uses a different `register(ctx)` signature
5. Gateway platform adapters need updates — the base adapter API changed

### From Gogeta pre-3.0 (early access)

1. Run `gogeta tools setup` to rebuild tool configuration
2. Run `gogeta curator run` to migrate skill usage tracking
3. Config files are forward-compatible — no manual migration needed

## Known Limitations

- **TUI on Windows** — the PTY bridge (dashboard → chat) uses `pywinpty` and may have rendering differences from native terminals
- **Gateway on Windows** — some platform adapters (Signal, Matrix) have limited Windows support due to native dependency requirements
- **Termux on Android** — the `termux` extra is stable but `termux-all` may have build failures for some native extensions
- **Electron desktop** — currently macOS and Linux only; Windows support pending
- **Kanban dispatcher** — systemd integration requires manual enable after install

## Roadmap

| Version | Focus |
|---------|-------|
| 3.1 | Windows desktop app, TUI polish, kanban web UI |
| 3.2 | Multi-modal agent, voice-native interaction, vision pipeline |
| 3.3 | Federated skill marketplace, plugin ecosystem expansion |
| 3.4 | Distributed agent mesh, cross-instance memory sharing |
| 4.0 | Autonomous agent operations, fleet management, enterprise auth |
