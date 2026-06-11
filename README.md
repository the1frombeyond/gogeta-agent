

```
 ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗ 
██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗
██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║
██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║
╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║
 ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝
```

<p align="center">
  <strong>v3.0 — The Self-Improving AI Agent by <a href="https://github.com/the1frombeyond">the1frombeyond</a></strong>
</p>

<p align="center">
  <a href="https://github.com/the1frombeyond/gogeta-agent"><img src="https://img.shields.io/badge/Docs-GitHub-FFD700?style=flat-square" alt="Documentation"></a>
  <a href="https://github.com/the1frombeyond/gogeta-agent"><img src="https://img.shields.io/badge/Source-GitHub-181717?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=flat-square" alt="中文"></a>
</p>

---

**GOGETA** is a self-improving AI agent that learns from experience and gets better the more you use it. It runs on a $5 VPS or a GPU cluster, works with any LLM provider, and you can talk to it from your terminal, Telegram, Discord, Slack, or a browser. One process, all platforms. It doesn't change when you change seats.

---

## Why GOGETA

Most agents are stateless helpers. You start a session, ask a question, and everything you taught them vanishes when you close the terminal. GOGETA keeps what it learns.

- **Closed-loop learning.** It creates skills from experience, improves them during use, and carries context across sessions. Over time it builds a real model of how you work.
- **Multi-platform by default.** One gateway process serves Telegram, Discord, Slack, WhatsApp, Signal, Matrix, email, SMS, and more. You talk to the same agent everywhere.
- **Provider-agnostic.** Bring your own model — OpenAI, Anthropic, Google, xAI, DeepSeek, OpenRouter, local models, 200+ endpoints. Switch mid-conversation with `/model`.
- **Runs anywhere.** Six terminal backends — local, Docker, SSH, Modal, Daytona, Singularity. Serverless backends hibernate when idle so you're not paying for nothing.
- **Extensible.** Skills, plugins, MCP servers, and an SDK for custom tools and providers.

---

## Core Features

| Capability | What it does |
|---|---|
| **CLI** | Rich terminal with autocomplete, skin engine, streaming tool output |
| **TUI** | React terminal UI with multiline editing, slash commands, session picker (`gogeta --tui`) |
| **Gateway** | Single daemon that bridges your agent to 15+ messaging platforms |
| **Skills** | Procedural memory as markdown — agent-authored, auto-improving, searchable |
| **Genome** | Experience-to-behavior learning pipeline — discovers patterns from how you work |
| **Lifeline** | Persistent identity (SOUL.md, session summaries, reflections, timeline) |
| **Plugins** | Memory backends, model providers, context engines, custom hooks |
| **Memory** | Pluggable backends (Honcho, Mem0, Supermemory, Hindsight, and more) |
| **Kanban** | Multi-agent work queue with SQLite boards, dispatcher, cross-profile collaboration |
| **Cron** | Natural-language scheduling — "every day at 9am" works. Multi-platform delivery. |
| **Tools** | 80+ built-in: terminal, files, web search, browser automation, vision, code execution |
| **Delegation** | Spawn isolated subagents for parallel work. Orchestrators can delegate recursively. |
| **Profiles** | Fully isolated instances — separate config, keys, memory, sessions per profile |
| **Dashboard** | Browser-based web dashboard with embedded TUI, session management, tool config |

---

## Quick Start

```bash
gogeta                  # Start chatting immediately
gogeta model            # Choose your LLM provider and model
gogeta tools            # Configure which tools are enabled
gogeta gateway          # Start Telegram, Discord, etc.
gogeta --tui            # React terminal UI
gogeta setup            # Guided setup wizard
gogeta doctor           # Diagnose config issues
```

### In conversation

```
/model openai:gpt-4o                              # Switch models mid-chat
/skills install official/github/pr-review          # Install a skill
/cron add "every day at 9am" "send me a summary"  # Schedule a job
/compress                                          # Compact context
/insights --days 30                                # Recent session review
```

---

## Installation

```bash
# Linux, macOS, WSL
curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash

# Windows (PowerShell)
iex (irm https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1)

# pip
pip install gogeta-agent[all]

# Docker
docker pull ghcr.io/the1frombeyond/gogeta-agent:latest

# Homebrew
brew install gogeta-agent

# Nix
nix run github:the1frombeyond/gogeta-agent
```

See [INSTALL.md](INSTALL.md) for every method and flag.

---

## Provider Support

GOGETA works with any OpenAI-compatible endpoint plus native integrations:

Nous Portal (300+ models), OpenRouter (200+), OpenAI, Anthropic, Google, xAI, DeepSeek, Mistral, AWS Bedrock, Azure, NVIDIA NIM, Hugging Face, MiniMax, NovitaAI, Ollama, and any custom endpoint.

Switch with `/model provider:model-name` mid-conversation. No restarts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GOGETA                                      │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │   CLI     │  │   TUI    │  │    Gateway        │  │   Dashboard  │ │
│  │ (rich)    │  │ (Ink)    │  │ (Telegram/Discord │  │ (Browser)    │ │
│  │           │  │          │  │  /Slack/WhatsApp  │  │             │ │
│  └─────┬─────┘  └────┬─────┘  └────────┬─────────┘  └──────┬──────┘ │
│        └──────────────┴─────────────────┴──────────────────┘        │
│                                   │                                 │
│                    ┌──────────────┴──────────────┐                  │
│                    │      AIAgent (run_agent.py)  │                  │
│                    │  ┌────────────────────────┐ │                  │
│                    │  │ Conversation Loop      │ │                  │
│                    │  │ Tool Orchestration     │ │                  │
│                    │  │ Budget Tracking        │ │                  │
│                    │  └────────────────────────┘ │                  │
│                    └──────────────┬──────────────┘                  │
│                                   │                                 │
│  ┌───────┐  ┌────────┐  ┌───────┴──────┐  ┌───────┐  ┌──────────┐ │
│  │ Tools │  │ Skills │  │  Providers   │  │Memory │  │  Plugins  │ │
│  │(80+)  │  │ System │  │(OpenAI/Ant..)│  │Backend│  │  System   │ │
│  └───────┘  └────────┘  └──────────────┘  └───────┘  └──────────┘ │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐ │
│  │  Cron    │  │  Kanban  │  │  Genome  │  │  Lifeline            │ │
│  │ Scheduler│  │ WorkQueue│  │ Learning │  │  (SOUL.md/Identity) │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

The core loop is synchronous with interrupt checking, budget tracking, and a one-turn grace call. Tools are auto-discovered via registry and grouped into toolsets per platform. The gateway runs as a daemon that dispatches messages from any platform to the same AIAgent instance.

---

## Skills

Skills are markdown files with frontmatter, prerequisites, procedures, and verification criteria. They're procedural memory — the agent reads them and follows the steps.

**Built-in:** `skills/` — always loadable. GitHub, MLOps, DevOps, Security, Creative, and more.

**Optional:** `optional-skills/` — shipped but not active by default. Autonomous agents, blockchain, communication, productivity, research, security.

Skills can be authored by the agent itself after complex tasks (auto-improving via the Curator), installed from the [Skills Hub](https://agentskills.io), created manually in `~/.gogeta/skills/`, or shared via the open agentskills.io standard.

```bash
gogeta skills list                     # Show installed skills
gogeta skills install official/<cat>/<name>  # Install from hub
gogeta skills create                   # Create a skill
gogeta curator status                  # Check curator state
```

---

## TUI

The TUI is a full React terminal application with chat streaming, tool activity feed, approval prompts, session picker, slash command autocomplete, and theming.

```bash
gogeta --tui
```

Architecture: TypeScript owns the screen (Ink), Python owns sessions, tools, and model calls. They talk over JSON-RPC over stdio.

The same TUI is embedded in the browser dashboard via PTY bridge — the Ink app runs inside an xterm.js terminal.

---

## Lifeline

Persistent identity and session memory:

- **SOUL.md** — core identity: name, purpose, principles, behavioral constraints
- **SESSION_SUMMARY.md** — compressed session summaries
- **REFLECTIONS/** — episodic memory at key decision points
- **Timeline** — structured records of build decisions, failures, recoveries

---

## Genome

The experience-to-behavior learning pipeline: pattern detection, workflow discovery, skill evolution, failure learning, confidence scoring, and dependency graph generation.

```python
from gogeta.genome import GenomeManager
gm = GenomeManager()
gm.learn()    # run the pipeline
gm.report()   # write genome.md
```

---

## Plugins

Two plugin surfaces:

1. **General plugins** — lifecycle hooks, custom tools, CLI subcommands, dashboard widgets
2. **Memory-provider plugins** — pluggable backends implementing the MemoryProvider ABC

Model-provider plugins are a separate lazy-discovery system. Each provider (OpenRouter, Anthropic, Gemini, etc.) ships as a plugin that registers a ProviderProfile.

```bash
gogeta plugin list         # List installed plugins
gogeta plugin install <name>  # Install a plugin
```

---

## Community & Contributing

- **Docs** — [github.com/the1frombeyond/gogeta-agent](https://github.com/the1frombeyond/gogeta-agent)
- **GitHub** — [github.com/the1frombeyond/gogeta-agent](https://github.com/the1frombeyond/gogeta-agent)
- **Issues** — [github.com/the1frombeyond/gogeta-agent/issues](https://github.com/the1frombeyond/gogeta-agent/issues)
- **Skills Hub** — [agentskills.io](https://agentskills.io)

### Development

```bash
git clone https://github.com/the1frombeyond/gogeta-agent.git
cd gogeta-agent
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

~17,000 tests across ~900 files. All tests run in isolated subprocesses for CI parity. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).

Built by **[the1frombeyond](https://github.com/the1frombeyond)**.
