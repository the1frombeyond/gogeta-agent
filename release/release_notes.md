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

- **Skin engine** — data-driven CLI theming with 4 built-in skins and user-installable YAML skins
- **TUI** — full Ink (React) terminal UI with JSON-RPC backend
- **Cron scheduler** — 4 schedule formats, 3-minute hard interrupt, multi-platform delivery
- **Kanban system** — durable SQLite-backed multi-agent work queue
- **Profiles** — fully isolated multi-instance support
- **Curator** — background skill lifecycle management
- **ACP adapter** — Agent Communication Protocol for IDE integration
- **Lifeline** — continuous agent loop with quality gates
- **Genome** — self-improving agent that evolves skills
- **Marketplace** — skill distribution through Skills Hub
- **Web dashboard** — localhost SPA with embedded TUI
- **Desktop app** — Electron chat application

## New Capabilities

- One-command installation via `curl -fsSL URL | bash`
- `gogeta doctor` — diagnostic tool
- `gogeta logs --follow` — real-time log streaming
- `gogeta cron` — full cron job lifecycle
- `gogeta kanban` — multi-agent work queue
- `gogeta curator` — skill lifecycle management
- `gogeta profile` — multi-instance profiles
- `gogeta skin` — live theme switching
- `gogeta tools` — curses-based toolset configuration

## Migration Notes

### From Hermes 2.x

1. Install Gogeta fresh — no migration script for Hermes config
2. Transfer API keys from `~/.hermes/.env` to `~/.gogeta/.env`
3. Transfer custom skills from `~/.hermes/skills/` to `~/.gogeta/skills/`
4. Plugin API is **not compatible** — different `register(ctx)` signature

### From Gogeta pre-3.0

1. Run `gogeta tools setup` to rebuild tool configuration
2. Config files are forward-compatible

## Known Limitations

- Gateway on Windows has limited Signal/Matrix support
- Electron desktop: macOS and Linux only
- Kanban dispatcher systemd service requires manual enable

## Roadmap

| Version | Focus |
|---------|-------|
| 3.1 | Windows desktop, TUI polish, kanban web UI |
| 3.2 | Multi-modal agent, voice-native interaction |
| 3.3 | Federated skill marketplace |
| 4.0 | Autonomous fleet management, enterprise auth |
