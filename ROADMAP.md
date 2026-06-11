# Gogeta 3.0 — Roadmap

---

## Gogeta 3.0 (Current — Shipped)

The self-improving AI agent platform by the1frombeyond. Version 3.0.

| Feature | Status | Description |
|---|---|---|
| **CLI** | ✅ Shipped | Rich + prompt_toolkit interactive terminal with autocomplete, history, skin engine, and KawaiiSpinner |
| **TUI** | ✅ Shipped | Full Ink (React) terminal UI via `gogeta --tui` with JSON-RPC bridge to Python backend |
| **Gateway** | ✅ Shipped | Single daemon bridging 20+ messaging platforms (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, email, SMS, DingTalk, WeCom, Feishu, QQ, and more) |
| **AIAgent** | ✅ Shipped | Core synchronous conversation loop with interrupt checking, iteration budget, and tool-calling LLM orchestration |
| **Skills System** | ✅ Shipped | Procedural memory as markdown skills — bundled (`skills/`), optional (`optional-skills/`), hub-installed, and agent-authored |
| **Genome** | ✅ Shipped | Experience-to-behavior learning pipeline: workflow discovery, pattern detection, skill evolution, failure learning, confidence scoring |
| **Lifeline** | ✅ Shipped | Persistent identity files (SOUL.md, session summaries, reflections, timeline, memories) |
| **Plugin System** | ✅ Shipped | PluginManager with lifecycle hooks, custom tools, CLI subcommands; three discovery paths (user, project, pip) |
| **Memory Providers** | ✅ Shipped | 8 pluggable backends: Honcho, Mem0, Supermemory, Byterover, Hindsight, Holographic, OpenViking, RetainDB |
| **Model Providers** | ✅ Shipped | 29 provider plugins: OpenAI, Anthropic, Google Gemini, xAI, DeepSeek, Mistral, OpenRouter, Nous Portal, AWS Bedrock, Azure, Ollama, Hugging Face, NVIDIA NIM, MiniMax, and more |
| **Kanban** | ✅ Shipped | SQLite-backed multi-agent work queue with dispatcher, board isolation, stale-claim recovery, and dashboard web UI |
| **Cron** | ✅ Shipped | Natural-language scheduled jobs with multi-platform delivery, 3-minute hard interrupt, catchup windows |
| **Profiles** | ✅ Shipped | Fully isolated multi-instance support — each profile has its own config, API keys, memory, sessions, and gateway state |
| **Dashboard** | ✅ Shipped | Browser-based web dashboard with embedded TUI, session management, tool configuration, and model picker |
| **Desktop App** | ✅ Shipped | Electron chat app with its own composer, transcript, and curated slash-command palette |
| **Tools** | ✅ Shipped | 80+ built-in tools: terminal, file operations, web search, browser automation, vision, code execution, delegation, TTS, image gen, cron job, memory, skills, kanban, computer use |
| **Delegation** | ✅ Shipped | Spawn isolated subagents for parallel work; orchestrator agents can recursively delegate |
| **Skin/Theme Engine** | ✅ Shipped | Data-driven CLI visual customization — 4 built-in skins, user YAML skins, per-element color/spinner/branding control |
| **ACP Adapter** | ✅ Shipped | Agent Communication Protocol server for VS Code / Zed / JetBrains IDE integration |
| **Event Bus** | ✅ Shipped | Synchronous in-process pub/sub with typed events, priority subscribers, middleware, and history buffer |
| **Intelligence System** | ✅ Shipped | Subscriber-based system on event bus: architectural decisions, project state, task tracking |
| **Session State** | ✅ Shipped | SQLite session store with FTS5 full-text search, WAL mode, compression-triggered session splitting |
| **Context Compression** | ✅ Shipped | Auto-summarization when approaching context limits; cache-aware to not break prompt caching |
| **Curator** | ✅ Shipped | Background skill lifecycle manager — usage tracking, LLM review, auto-archive (never deletes) |
| **Docker** | ✅ Shipped | Docker Compose with s6-overlay supervision, multi-architecture support |
| **Nix** | ✅ Shipped | Flake-based Nix deployment |
| **Provider Routing** | ✅ Shipped | Per-task model routing via `auxiliary` config; OpenRouter provider selection (throughput/latency/price) |
| **Cross-Platform** | ✅ Shipped | Linux, macOS, Windows (native + WSL2); Windows footgun checker script |

---

## Gogeta 3.1 (In Progress)

Items with implementation plans written but not yet shipped.

| Feature | Status | Description |
|---|---|---|
| **OpenAI-Compatible API Server** | 🏗️ Planned | Expose a REST `/v1/chat/completions` and `/v1/responses` endpoint so any OpenAI-compatible frontend (Open WebUI, LobeChat, LibreChat, NextChat) can use Gogeta as a backend. See `.plans/openai-api-server.md`. |
| **LLM Response Streaming** | 🏗️ Planned | Token-by-token streaming across all platforms (CLI, gateway, API server) via callback-based architecture. Off by default, feature-flagged. See `.plans/streaming-support.md`. |
| **Gemini OAuth Provider** | 🏗️ Planned | First-class Gemini provider authenticating via Google OAuth (PKCE) — browser-based auth without manual API keys. See `plans/gemini-oauth-provider.md`. |

---

## Gogeta 3.2+ (Future)

Larger features and enhancements beyond the immediate roadmap.

| Feature | Status | Description |
|---|---|---|
| **Real SSE Streaming** | 🔮 Future | Replace single-chunk pseudo-streaming with real token-by-token SSE in the API server (Phase 4 of streaming plan) |
| **Gateway Streaming** | 🔮 Future | Progressive message editing on Telegram, Discord, Slack during streaming (Phase 2 of streaming plan) |
| **CLI Streaming** | 🔮 Future | Live token display in prompt_toolkit with batch accumulation (Phase 3 of streaming plan) |
| **Tool Call Transparency** | 🔮 Future | Opt-in mode for API server to emit tool_call/tool_result events so agent-aware frontends see the full agent workflow |
| **Model Passthrough** | 🔮 Future | Let API server clients override the server-side model via the `model` field in requests |
| **CORS Support** | 🔮 Future | Proper CORS headers for browser-based frontends connecting to the API server |
| **Enhanced Marketplace** | 🔮 Future | Better skills marketplace integration, reviews, ratings, and discoverability beyond the current hub |
| **Plugin SDK** | 🔮 Future | Formalized plugin SDK with documentation templates, generators, and testing harnesses |
| **Hierarchy System** | 🔮 Future | Agent role/authority hierarchy system (directory reserved at `gogeta/hierarchy/`) |
| **More Terminal Backends** | 🔮 Future | Additional terminal execution environments beyond the current 6 (local, Docker, SSH, Modal, Daytona, Singularity) |
| **Kanban Enhancements** | 🔮 Future | Improved dashboard, richer dispatch strategies, cross-board workflows |

---

## Backlog

Ideas not yet prioritized or scheduled.

| Feature | Description |
|---|---|
| **Multi-Model Orchestration** | Route sub-tasks to different models based on capability (vision, code, reasoning) within a single conversation |
| **Agent Swarms** | Coordinated multi-agent teams beyond the current kanban/dispatch model |
| **Visual Skill Builder** | GUI for creating and editing SKILL.md files without markdown |
| **Skill Testing Framework** | Automated sandbox for testing skills before publishing to the hub |
| **Mobile Companion App** | Native mobile app for iOS/Android to interact with running gateways |
| **Offline Mode** | Run fully offline with local LLMs (Ollama, llama.cpp) and no cloud dependencies |
| **Advanced Analytics** | Usage dashboards, cost tracking, token consumption by session/provider |
| **Knowledge Graph UI** | Visual browser for the genome's workflow graph and learned patterns |
| **Federated Skills Hub** | Decentralized skills registry — publish and consume skills without a central server |
| **Multi-User Gateway** | Per-user session isolation and authentication within a single gateway instance |
| **Template System** | Pre-built agent templates for common roles (developer, researcher, DevOps) with tailored tool/skill presets |
| **Agent Sandbox** | Isolated environment for testing agent behavior with mocked LLM responses and deterministic tool results |
| **Plugin Scaffolding CLI** | `gogeta plugin create` command that generates boilerplate for new plugins |
| **Auto-Update Channels** | Stable/nightly release channels with automatic in-place updates |
