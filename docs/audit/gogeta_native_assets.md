# Gogeta Native Assets Audit

Date: 2026-06-07
Auditor: Architecture Engine (Phase 1 pre-audit)

---

## Table of Contents

1. [TUI (`tui/`)](#1-tui)
2. [Skills (`skills/`)](#2-skills)
3. [Lifeline (`lifeline/`)](#3-lifeline)
4. [Tools (`tools/`)](#4-tools)
5. [Cross-System Analysis](#5-cross-system-analysis)
6. [Priority Recommendations](#6-priority-recommendations)

---

## 1. TUI

### Location
`tui/` (TypeScript + Ink/React terminal UI)

### Structure
```
tui/
├── src/
│   ├── index.tsx              (70 lines)  Entry point
│   ├── app.tsx                (5 lines)   App root
│   ├── theme.ts               (51 lines)  Dark + light themes
│   ├── types/
│   │   ├── index.ts           (1 line)    Re-exports
│   │   └── theme.ts           (30 lines)  Theme interfaces
│   ├── stores/
│   │   ├── chat-store.ts      (192 lines)  Zustand chat state
│   │   ├── config-store.ts    (65 lines)   Zustand config state
│   │   └── ui-store.ts        (65 lines)   Zustand UI state
│   ├── lib/
│   │   ├── bridge.ts          (332 lines)  JSON-RPC gateway client
│   │   ├── config.ts          (100 lines)  Config loader + defaults
│   │   ├── format.ts          (22 lines)   Display formatters
│   │   ├── gradient.tsx       (15 lines)   Gold gradient text
│   │   ├── input.ts           (73 lines)   Command definitions
│   │   ├── session.ts         (97 lines)   JSON session persistence
│   │   ├── skills.ts          (35 lines)   Skill discovery
│   │   └── slash-handler.ts   (293 lines)  Slash command routing
│   └── components/
│       ├── app-frame.tsx      (10 lines)   Layout wrapper
│       ├── app-layout.tsx     (62 lines)   Main layout router
│       ├── header.tsx         (16 lines)   Session header
│       ├── message-list.tsx   (207 lines)  Chat transcript renderer
│       ├── input-bar.tsx      (39 lines)   Input display
│       ├── input-handler.tsx  (112 lines)  Keyboard input handler
│       ├── welcome.tsx        (55 lines)   Welcome/banner screen
│       ├── status-bar.tsx     (18 lines)   Bottom status line
│       ├── command-dropdown.tsx (36 lines) Slash command autocomplete
│       ├── config-screen.tsx  (151 lines)  Modal config editor
│       ├── search-overlay.tsx (83 lines)   Message search UI
│       ├── session-browser.tsx (90 lines)  Session list browser
│       └── setup-wizard.tsx   (569 lines)  First-run setup wizard
├── dist/                      (compiled output)
├── package.json               (Ink 5, React 18, Zustand 4)
├── tsconfig.json              (ES2022, NodeNext)
└── tui.cmd                    (launcher)
```

### Total Size
~1,197 lines of TypeScript across 20 source files. Average file ~60 lines.

### Current Capabilities
- **Conversation-first chat UI** with role-colored messages (user/assistant/system/tool)
- **Markdown rendering** in the transcript: code blocks with syntax labels, blockquotes, lists, numbered lists, headings, horizontal rules
- **Slash command system** with 22 commands across 7 categories (session, model, AI, dev, UI, system, agent)
- **Command dropdown** with autocomplete filtering as user types `/`
- **Session persistence** to `~/.gogeta/sessions/*.json` with metadata indexing
- **Session browser** with load/delete, metadata preview (date, message count, preview text)
- **Full-text message search** within the current session
- **Configuration screen** with model, MCP, skills, and UI tabs
- **First-run setup wizard** with 7-step guided configuration (name, AI name, provider, API key, terminal backend, messaging platforms, tools)
- **Gateway connection** via stdio JSON-RPC to Python backend (`tui_gateway/`)
- **Streaming response** rendering with real-time content display
- **Tool call visualization** with success/failure indicators
- **Status bar** showing current model name
- **Dark and light themes** with gold/corsair color palette (Gogeta branding)
- **Gradient "gogeta" text** in gold tones
- **Clean typing** with Zod-compatible TypeScript interfaces

### Unique Value (What Gogeta Does NOT Have)
1. **Standalone Ink-based TUI** — Gogeta has `ui-tui/` also built with Ink, but Gogeta's TUI is a separate, independently-runnable implementation with different architecture (direct zustand stores vs. Gogeta's nanostore approach)
2. **First-run setup wizard** — Gogeta has `gogeta setup` but as a CLI wizard, not a TUI-embedded interactive flow
3. **Gogeta branding** — Gold/corsair color scheme, "Gogeta CLI v3.0.0" banner, ASCII art logo, gradient text. This is not a Gogeta reskin.
4. **Simpler session model** — JSON file-based (vs Gogeta's SQLite FTS5), which trades search power for zero-dependency simplicity
5. **Independent gateway client** — Gogeta's TUI bridges to a Python gateway process, but the bridge protocol is simpler than Gogeta's `tui_gateway`
6. **Config as JSON** — `~/.gogeta/config.json` is a flat JSON file, vs Gogeta's YAML-based `~/.gogeta/config.yaml`

### Technical Debt
| Issue | Severity | Details |
|-------|----------|---------|
| No tests | HIGH | No test files found in the TUI directory |
| Gateway client assumes local Python | MEDIUM | `bridge.ts` hardcodes `python`/`python3` path discovery |
| No error recovery on gateway disconnect | MEDIUM | The gateway client sets `connected=false` but doesn't auto-reconnect |
| Session persistence uses JSON files | LOW | Works fine for single-user TUI but lacks FTS5 search, crash recovery, export |
| In-memory chat state only | MEDIUM | Messages are only persisted when `beforeExit` fires — crash during a session loses data |
| No tool output limits | LOW | Tool results in `bridge.ts` hard-slice at 500 chars |
| Config screen is read-only | LOW | Shows config but requires `/model`, `/provider`, `/mcp` commands to change |
| Slash command names hardcoded | MEDIUM | `slash-handler.ts` has all 22 commands inline, no registry pattern |
| Empty features in welcome | LOW | "Channels", "Arena", "Auto-learn" features listed but not functional |
| No cost tracking UI | LOW | `ui-store.ts` has `costUsd` field but it's never populated in the UI |

### Dependencies
- **Runtime:** Node.js, Ink 5, React 18, Zustand 4
- **Build:** TypeScript 5, tsc
- **Backend:** Python (tui_gateway), the Python process must be discoverable
- **Data:** `~/.gogeta/` directory with `config.json` and `sessions/`

### Architecture Fit
The TUI is a **presentation layer only** — it delegates all AI interaction to the Python gateway. It fits naturally as a frontend in the Gogeta architecture, needing only:
- A more robust gateway protocol
- Integration with the future Session Platform (SQLite)
- Integration with the future Context Engine
- Integration with the future Cost Intelligence
- A proper plugin system for slash commands

### Recommendation
**KEEP + MODERNIZE**

- Keep the Ink/React stack and Zustand stores
- Replace JSON session persistence with SQLite-backed SessionDB
- Add integration tests and component tests
- Fix the crash-recovery gap (periodic auto-save)
- Add gateway auto-reconnect
- Externalize slash commands into a plugin registry
- Replace the inline gateway client with the unified Event Bus
- Add cost display and architecture status indicators

---

## 2. Skills

### Location
`skills/` (directory of skill subdirectories + standalone .py files)

### Structure
```
skills/
├── base.py                      (6 lines)    Skill base class
├── registry.json                (502 lines)   Skill catalog with 40+ entries
├── features.py                                (skill feature flags)
├── tools.py                                   (skill tool helpers)
├── agent_browser_skill/                       (browser automation)
│   ├── SKILL.md
│   └── agent_browser.py
├── browser_harness_skill/                     (advanced CDP browser)
├── browser_use_skill/                         (autonomous web agent)
├── web_search_skill/                          (web search tool)
├── web_browser.py                             (standalone web browser tool)
├── github_skill/                              (gh CLI integration)
│   ├── SKILL.md
│   └── github_skill.py
├── mcp_builder_skill/                         (MCP server builder)
├── skill_creator_skill/                       (skill authoring)
├── skill_stealer_skill/                       (cross-platform skill import)
├── code_executor_skill/                       (sandboxed code execution)
├── ai_reasoning_skill/                        (local LLM reasoning)
├── self_improvement_skill/                    (continuous learning loop)
├── file_learner_skill/                        (project pattern analysis)
├── ontology_skill/                            (entity-relation knowledge graph)
├── tiered_memory_skill/                       (HOT/WARM/COLD memory tiers)
├── voice_skill/                               (Edge-TTS speech synthesis)
├── voice_id_skill/                            (biometric voice ID)
├── translator_skill/                          (100+ language translation)
├── notes_skill/                               (journaling system)
├── gog_skill/                                 (Google Services integration)
├── file_manager_skill/                        (local file management)
├── system_monitor_skill/                      (real-time system monitoring)
├── news_skill/                                (news aggregation)
├── weather_skill/                             (weather forecasts)
├── network_tools_skill/                       (ping, DNS, port scan)
├── docker_skill/                              (Docker management)
├── media_skill/                               (image/audio/video metadata)
├── data_analysis_skill/                       (CSV/JSON/Excel analysis)
├── database_skill/                            (SQLite management)
├── crypto_skill/                              (hash/encrypt/sign)
├── email_skill/                               (SMTP/IMAP email)
├── automation_skill/                          (cron scheduling)
├── desktop_control.py                         (mouse/keyboard/window automation)
├── screen_reader.py                           (OCR screen reading)
├── system_info.py                             (hardware/OS info)
├── system_control.py                          (power management)
├── docx_handler.py                            (Word document creation)
├── pptx_handler.py                            (PowerPoint creation)
├── apple/                                     (Apple ecosystem skills)
├── autonomous-ai-agents/                      (agent workflow skills)
├── creative/                                  (creative tool skills)
├── data-science/                              (data science skills)
├── devops/                                    (infrastructure skills)
├── email/                                     (email-specific skills)
├── github/                                    (additional GitHub skills)
├── media/                                     (additional media skills)
├── mlops/                                     (ML pipeline skills)
├── note-taking/                               (note-taking workflow skills)
├── productivity/                              (productivity skills)
├── research/                                  (research skills)
├── smart-home/                                (home automation skills)
├── social-media/                              (social platform skills)
├── software-development/                      (development workflow skills)
├── red-teaming/                               (security testing skills)
├── yuanbao/                                   (Tencent Yuanbao skills)
├── index-cache/                               (skill indexing cache)
├── dogfood/                                   (internal testing skills)
├── ├── ... (various skill files)
```

### Total Size
~40+ registered skills in the catalog, plus multiple unregistered skill subdirectories. Ranges from single-file Python scripts to multi-file skill packages with SKILL.md + .py.

### Current Capabilities
- **Registry-driven discovery** via `registry.json` (version 2) with builtin, community, and skills.sh sources
- **SKILL.md metadata standard** with frontmatter: name, description, version, author, triggers, category
- **Skill categorization** into 12 categories: browser, development, AI, productivity, system, knowledge, voice, files, network, media, automation, data
- **Trigger-driven activation** — each skill lists trigger phrases that determine when it's invoked
- **Mixed delivery** — skills can be pure instruction (SKILL.md only) or include executable Python scripts
- **Version tracking** per skill with author metadata
- **Multi-registry support** — builtin, community (GitHub), and skills.sh registries
- **Installation tracking** via `installed` boolean in registry

### Unique Value (What Gogeta Does NOT Have)
1. **Self-Improvement Skill** — An automated continuous learning loop (`self_improvement_skill`) that captures insights, errors, and feature requests to evolve the system. This is a **Gogeta/JARVIS-native concept** not present in Gogeta.
2. **Tiered Memory Skill** — A HOT/WARM/COLD memory tier system with lifecycle rules (promotion after 3 uses in 7 days, demotion after 30 days, archiving after 90). This is a **Gogeta/JARVIS-native skill**.
3. **Ontology Skill** — Entity-relation knowledge graph stored in JSONL, with schema validation. A structured knowledge representation system not mirrored in Gogeta.
4. **Skill Stealer** — Autonomous skill acquisition from other AI platforms. A meta-capability for cross-platform skill porting.
5. **File Learner** — Analyzes workspace files to extract coding patterns, project structures, and style conventions. Generates task-specific AGENTS.md content.
6. **"JARVIS Core" authorship** — The skill ecosystem is branded as JARVIS, not Gogeta. These skills were authored for the Gogeta/JARVIS project.
7. **Trigger-based invocation model** — Skills define natural language triggers that determine when they're activated. This is distinct from Gogeta's toolset-based model.

### Technical Debt
| Issue | Severity | Details |
|-------|----------|---------|
| Unregistered skills | HIGH | Many skill subdirectories (apple/, devops/, creative/, etc.) exist but are NOT in `registry.json` — they're invisible to the system |
| No skill versioning enforcement | MEDIUM | `version` field exists in metadata but no upgrade/rollback mechanism |
| Dead standalone scripts | MEDIUM | `features.py`, `tools.py` at root level with unclear purpose |
| Mixed Python/instruction models | MEDIUM | Some skills are .md only, some are .py only, some are both — no consistent execution model |
| No skill dependencies | LOW | Skills can't declare dependencies on other skills |
| No skill testing framework | MEDIUM | No standardized test pattern for skill verification |
| No skill analytics | LOW | No usage tracking at the skill level |
| No permission model | MEDIUM | Skills run with full agent permissions |
| base.py is vestigial | LOW | 6-line base class that's not actually used by the registry system |
| Registry.json duplicates filesystem | MEDIUM | Skills must be in both registry.json AND on disk — no single source of truth |

### Dependencies
- Python 3 for .py skill scripts
- Various: gh CLI (github), Docker (docker), Edge-TTS (voice), etc.
- No formal dependency declaration system

### Architecture Fit
The skills system is an **instruction library** for the agent — it provides context and scripts that shape agent behavior. It fits as a **content layer** above the tool platform. Key integration points:
- Should be consumed by the Context Engine (inject relevant skills into system prompt)
- Should be registered in the Tool Registry for executable skill scripts
- Should be versioned and searchable through the knowledge platform

### Recommendation
**KEEP + MODERNIZE**

- Consolidate all skills under a unified discovery mechanism (move unregistered skills into `registry.json`)
- Migrate from `registry.json` to the Platform-neutral Tool Registry
- Add version checking and dependency declarations to SKILL.md
- Add skill analytics (usage counts, success rates)
- Create a skill testing framework
- Remove dead files (root-level `features.py`, `tools.py`)
- Connect to the future Context Engine for relevance-based injection
- The Self-Improvement, Tiered Memory, and Ontology skills should be **upgraded to core platform capabilities** rather than remaining as agent-prompt skills

---

## 3. Lifeline

### Location
`lifeline/` (markdown files + JSON directories)

### Structure
```
lifeline/
├── SOUL.md          (24 lines)  Core identity declaration
├── IDENTITY.md      (30 lines)  Active memory systems registry
├── USER.md          (16 lines)  User profile (template)
├── MEMORIES.md      (16 lines)  Memory index (template)
├── TIMELINE.md      (14 lines)  Chronological event log (template)
├── WORLDSTATE.md    (16 lines)  Current context snapshot (template)
├── LEGACY.md        (17 lines)  Long-term goals and milestones
├── ENERGY.md        (13 lines)  System health metrics (template)
├── FAILURES.md      (13 lines)  Error log and corrections (template)
├── RITUALS.md       (12 lines)  Habit tracking (template)
├── TASTES.md        (14 lines)  User preferences (template)
├── SYSTEM_RULES.md  (19 lines)  Operational constraints
├── REFLECTIONS/     (3 JSON files) Post-task reflections
│   ├── reflection_20260526_060523.json
│   ├── reflection_20260529_113620.json
│   └── reflection_20260529_121219.json
├── JOURNAL/         (4 JSON files) Session journals
│   ├── 2026-05-26_05-40-52.json
│   ├── 2026-05-26_06-05-23.json
│   ├── 2026-05-29_11-36-20.json
│   └── 2026-05-29_12-12-19.json
├── THOUGHTS/        (empty)     Dedicated thought storage
├── MISSIONS/        (empty)     Active mission definitions
├── DREAMS/          (empty)     Aspirational goals
└── SKILLS/          (empty)     Generated skill output
```

### Current Capabilities
- **Agent identity declaration** via `SOUL.md` — defines mission, principles, behavioral rules, and safety constraints
- **Memory engine registry** in `IDENTITY.md` — declares 15 conceptual memory engines (Temporal Drift, Negative Space, Emotional Residue, Predictive Regret, Context Bleed, Micro Habits, Counterfactual, etc.)
- **Operational constraints** in `SYSTEM_RULES.md` — 9 rules covering safety, behavior, and operational boundaries
- **Reflection recording** — JSON-formatted post-task reflections with task summary, lessons, critique verdict, and links to journal entries
- **Journal logging** — Timestamped JSON journal entries that track session activity
- **Long-term planning** via `LEGACY.md` — 5 long-term objectives and milestone tracking
- **User profile template** in `USER.md` — placeholder for user identity, preferences, workflows, and habits
- **Timeline format** in `TIMELINE.md` — structured chronological log format (populated manually)
- **Failure tracking** in `FAILURES.md` — error log and correction patterns (template)
- **Energy/performance** in `ENERGY.md` — system health monitoring template
- **Preference learning** in `TASTES.md` — user communication and tool preferences

### Unique Value (What Gogeta Does NOT Have)
1. **Persistent agent identity** — Gogeta has no `SOUL.md` or identity declaration system. The Lifeline is a **fundamentally unique concept**.
2. **15 conceptual memory engines** — IDENTITY.md lists 15 advanced memory concepts (Temporal Drift, Negative Space, Emotional Residue, Predictive Regret, etc.) that have no equivalent in Gogeta. While most are currently aspirational/declarative, the architecture concept is unique.
3. **Reflection loop** — Post-task reflection generation that captures lessons and generates journal entries. Gogeta has a Curator system for skill maintenance but no general reflection system.
4. **Structured behavioral rules** — `SYSTEM_RULES.md` and `SOUL.md` define agent behavioral constraints inline, not just in system prompts.
5. **Mission/thought/reflection storage** — Directories for persistent agent cognition artifacts that survive session boundaries.
6. **Declarative memory architecture** — The identity doc explicitly names the memory systems the agent believes it has, creating a self-fulfilling architecture prompt.

### Technical Debt
| Issue | Severity | Details |
|-------|----------|---------|
| 6 of 18 files are empty directories | HIGH | THOUGHTS/, MISSIONS/, DREAMS/, SKILLS/ have zero content |
| 8 files are templates without auto-population | HIGH | USER.md, MEMORIES.md, TIMELINE.md, WORLDSTATE.md, ENERGY.md, FAILURES.md, RITUALS.md, TASTES.md all contain placeholder text like "[To be learned]" |
| 15 memory engines are aspirational | HIGH | IDENTITY.md declares 15 memory engines as "Online" but none have actual implementation — they're prompts, not systems |
| No automated updates | MEDIUM | TIMELINE.md, WORLDSTATE.md, ENERGY.md are manually updated or not at all |
| Reflection format is basic | MEDIUM | Reflections store single "verdict: passed/failed" critique — no structured lesson extraction |
| JOURNAL and REFLECTIONS reference each other | LOW | Files contain path references to a different base path (`C:\Users\the1frombeyond\Documents\jarvis\`) |
| No integration with session system | MEDIUM | Lifeline is separate from the session store — no cross-referencing |
| Only 3 reflections, 4 journals | LOW | Evidence of minimal real usage |

### Dependencies
- Python for reflection/journal generation
- File system for storage
- No database, no external services

### Architecture Fit
The Lifeline is a **persistent agent identity and reflection layer**. It's one of Gogeta's most architecturally unique assets. It should become:
- The foundation of the **Project Intelligence** system (Phase 10)
- Integrated with the **Memory System** (facts go to memory, lessons go to lifeline)
- The basis for the **Reflection Engine** (automated post-task analysis)
- Connected to the **Session Platform** (journal entries link to sessions)
- The identity source for **Agent branding** (gogeta identity flows from SOUL.md)

### Recommendation
**KEEP + INTEGRATE**

- This is Gogeta's most architecturally unique asset. **Do not remove or replace.**
- Upgrade empty templates to auto-populated systems:
  - TIMELINE.md → auto-generated from session data
  - WORLDSTATE.md → auto-detected system state
  - USER.md → learned from interaction patterns
  - ENERGY.md → from performance monitoring
- The 15 memory engines should either be:
  - Actually implemented as memory providers, or
  - Condensed into a documented architecture concept with the realistic subset implemented
- Connect REFLECTIONS to the Session Platform (each reflection links to a session)
- Connect JOURNAL to the Event Bus (journal entries published as events)
- Make SOUL.md the identity source for the entire Gogeta platform (TUI branding, CLI banner, all user-facing identity)

---

## 4. Tools

### Location
`tools/` (92 Python files)

### Structure
```
tools/
├── __init__.py          (25 lines)  Package namespace, check_file_requirements
├── registry.py          (589 lines) ToolRegistry singleton, ToolEntry, AST auto-discovery
├── permissions.py                   Tool permission checking
├── approval.py                      Approval flow
├── budget_config.py                 Tool budget/rate limits
├── path_security.py                 Path traversal prevention
├── url_safety.py                    URL safety validation
├── threat_patterns.py               Threat detection patterns
├── tirith_security.py               TIRITH security rules
├── schema_sanitizer.py              Schema sanitization
├── tool_output_limits.py            Output size limits
├── tool_result_storage.py           Result persistence
├── fuzzy_match.py                   Fuzzy matching utilities
├── env_passthrough.py               Environment passthrough
├── env_probe.py                     Environment probing
├── lazy_deps.py                     Lazy dependency loading
├── auto_detect.py                   Auto-detection utilities
├── ansi_strip.py                    ANSI code stripping
├── checkpoint_manager.py            Session checkpoint management
├── file_operations.py               File operation utilities
├── file_state.py                    File state tracking
├── file_tools.py                    File read/write/list
├── terminal_tool.py                 Shell command execution
├── delegate_tool.py                 Subagent spawning
├── memory_tool.py                   Curated memory read/write
├── browser_tool.py                  Playwright browser automation
├── browser_cdp_tool.py              CDP browser control
├── browser_camofox.py               Camofox browser
├── browser_camofox_state.py         Camofox state
├── browser_dialog_tool.py           Browser dialog handling
├── browser_supervisor.py            Browser supervision
├── web_tools.py                     Web browsing + extraction
├── search_tools.py                  Web search
├── code_execution_tool.py           Sandboxed code execution
├── computer_use_tool.py             Computer use (UI automation)
├── computer_use/                    Computer use backend
├── vision_tools.py                  Image analysis
├── image_generation_tool.py         Image generation
├── video_generation_tool.py         Video generation
├── tts_tool.py                      Text-to-speech
├── transcription_tools.py           Audio transcription
├── mcp_tool.py                      MCP client
├── mcp_oauth.py                     MCP OAuth flow
├── mcp_oauth_manager.py             MCP OAuth management
├── skill_manager_tool.py            Skill lifecycle
├── skill_provenance.py              Skill origin tracking
├── skill_usage.py                   Skill usage stats
├── skills_ast_audit.py              Skill AST analysis
├── skills_guard.py                  Skill safety guard
├── skills_sync.py                   Skill synchronization
├── skills_tool.py                   Skill execution
├── skills_hub.py                    Skill hub/discovery
├── kanban_tools.py                  Kanban board tools
├── cronjob_tools.py                 Cron job management
├── todo_tool.py                     Todo list management
├── session_search_tool.py           Session FTS5 search
├── task_tools.py                    Task management
├── superpower_tools.py              Superpower activation
├── clarify_tool.py                  Clarification tool
├── clarify_gateway.py               Clarification gateway
├── send_message_tool.py             Message sending
├── feishu_doc_tool.py               Feishu document
├── feishu_drive_tool.py             Feishu drive
├── discord_tool.py                  Discord integration
├── homeassistant_tool.py            Home Assistant
├── yuanbao_tools.py                 Yuanbao integration
├── microsoft_graph_auth.py          Microsoft auth
├── microsoft_graph_client.py        Microsoft Graph
├── x_search_tool.py                 X/Twitter search
├── xai_http.py                      xAI HTTP client
├── openrouter_client.py             OpenRouter client
├── grounding_tools.py               Fact grounding
├── mixture_of_agents_tool.py        MoA orchestration
├── voice_mode.py                    Voice mode
├── debug_helpers.py                 Debug utilities
├── migration.py                     Migration helpers
├── interrupt.py                     Interrupt handling
├── thread_context.py                Thread context
├── osv_check.py                     OSV vulnerability check
├── patch_parser.py                  Patch parsing
├── credential_files.py              Credential file management
├── binary_extensions.py             Binary extension detection
├── managed_tool_gateway.py          Managed tool gateway
├── slash_confirm.py                 Slash command confirmation
├── tool_search.py                   Tool search
├── tool_backend_helpers.py          Tool backend helpers
├── website_policy.py                Website policy
├── fal_common.py                    FAL AI common
├── neutts_synth.py                  NEUTTS synthesis
├── neutts_samples/                  NEUTTS samples
└── environments/                    Terminal backends (local, docker, ssh, modal, daytona, singularity)
```

### Total Size
589 lines in `registry.py` (core), 92 total Python files.

### Current Capabilities
- **Singleton ToolRegistry** (`registry.py`) with thread-safe registration, deregistration, schema collection, dispatch, and availability checking
- **AST-based auto-discovery** of tools — `discover_builtin_tools()` scans `tools/*.py` for `registry.register()` calls and imports them automatically
- **ToolEntry** with full metadata: name, toolset, schema (JSON), handler, check_fn, requires_env, is_async, description, emoji, max_result_size_chars, dynamic_schema_overrides
- **TTL-cached availability checks** (30-second cache for `check_fn` results)
- **Generation counter** for cache invalidation on registry mutations
- **Toolset aliases** for flexible tool grouping
- **Conflict detection** — prevents accidental tool shadowing across toolsets (with `override=True` opt-in)
- **MCP dynamic tool discovery** — MCP servers can add/remove tools at runtime
- **Async handler bridging** — `_run_async()` bridges async handlers
- **Error sanitization** — `_sanitize_tool_error()` prevents framing tokens in error messages
- **Security tools** — path_security, url_safety, threat_patterns, tirith_security for defensive tool execution
- **Comprehensive tool catalog** — 15+ tool categories covering terminal, file, web, browser, code execution, memory, skills, image/audio/video generation, MCP, delegation, kanban, cron, todo, search, messaging platforms, and more
- **Tool helper utilities** — `tool_error()`, `tool_result()` for consistent JSON response formatting
- **Per-tool results size limits** via `max_result_size_chars`

### Unique Value (What Gogeta Does NOT Have)
In practice, the `tools/` directory in this repository is the **same tools system used by Gogeta**. The registry, the auto-discovery, the patterns — all originated from Gogeta Agent development. The Gogeta-native value is:
1. **Per-tool emoji** — metadata field for visual tool identification
2. **Some unique tools** — `x_search_tool.py`, `fal_common.py`, `neurts_synth.py`, `grounding_tools.py` may have Gogeta-specific implementations
3. **The tool-to-skill pipeline** — `skills_guard.py`, `skills_ast_audit.py`, `skills_sync.py` form a Gogeta-specific skill quality pipeline

However, the tools system is largely **shared infrastructure** rather than unique Gogeta IP. Its value is that it's already mature, tested, and functional.

### Technical Debt
| Issue | Severity | Details |
|-------|----------|---------|
| Module-level side effects | HIGH | All tool files call `registry.register()` at import time — makes testing and lazy loading harder |
| Global mutable singleton | MEDIUM | `registry = ToolRegistry()` at module level — cannot have isolated registries for testing |
| Circular import chain documented but fragile | MEDIUM | `registry.py → tools/*.py → model_tools.py → run_agent.py` must be maintained carefully |
| check_fn TTL is arbitrary | LOW | 30-second cache is a guess — should be configurable or event-driven |
| No tool analytics | MEDIUM | No usage tracking, no performance metrics per tool |
| MCP tool refresh is nuclear | MEDIUM | `deregister()` + full re-register on every MCP `notifications/tools/list_changed` |
| `model_tools.py` still has procedural orchestration | MEDIUM | `get_tool_definitions()`, `handle_function_call()`, `check_tool_availability()` exist in `model_tools.py`, not in the registry |
| No permission model per tool | MEDIUM | `permissions.py` exists but no per-tool ACL system |
| No tool versioning | LOW | Tools don't declare versions |
| Helpers spread across files | LOW | `tool_result()`, `tool_error()` in registry.py; `_sanitize_tool_error()`, `_run_async()` in model_tools.py |

### Dependencies
- Python 3 stdlib (ast, importlib, json, logging, threading, time, pathlib, typing)
- Various per-tool dependencies: playwright, docker, modal, etc.
- No framework dependencies for the registry itself

### Architecture Fit
The Tools system is already close to what Phase 3's "Tool Platform" describes. The `ToolRegistry` is effectively the **Unified Tool Registry** called for in the roadmap. Key gaps:
- **Tool Discovery** — exists via AST scanning but needs explicit registration as well
- **Tool Metadata** — exists in `ToolEntry` but needs categories, tags, and documentation links
- **Tool Permissions** — exists but needs per-tool ACL and user approval flows
- **Tool Analytics** — does not exist, needs usage tracking and cost attribution
- **Tool Categories** — implicit via `toolset` field but needs explicit category definitions with hierarchy

### Recommendation
**KEEP + MERGE + UPGRADE**

- The ToolRegistry is the foundation for Phase 3. **Don't rewrite it.**
- Merge the registry into the new Gogeta Tool Platform:
  - Extract `model_tools.py` orchestration functions into the registry
  - Add analytics hooks
  - Add explicit permission system (per-tool, per-user)
  - Add tool categories with hierarchy
  - Replace module-level `registry.register()` with explicit discovery
- Add tool versioning and dependency declarations
- Add per-tool cost tracking
- Remove or consolidate: `neutts_samples/` (move to assets), `fal_common.py` (move to providers)

---

## 5. Cross-System Analysis

### What Gogeta Has That Gogeta Does Not

| Capability | Where | Gogeta Equivalent |
|------------|-------|-------------------|
| SQLite FTS5 session store | `gogeta_state.py` | JSON file sessions (TUI) |
| Slash command registry pattern | `gogeta_cli/commands.py` | Inline in `slash-handler.ts` |
| Skin engine | `gogeta_cli/skin_engine.py` | Hardcoded dark/light themes |
| Multi-profile support | `gogeta_cli/main.py` | Single-profile |
| Plugin system | `gogeta_cli/plugins.py` | Not present |
| Curator (skill lifecycle) | `agent/curator.py` | Not present |
| Kanban (multi-agent queue) | `plugins/kanban/` | Not present |
| Cron scheduler | `cron/` | Not present |
| Gateway (platform adapters) | `gateway/` | Not present |
| ACP adapter | `acp_adapter/` | Not present |
| i18n | `locales/` | Not present |

### What Gogeta Has That Gogeta Does Not

| Capability | Location | Unique Value |
|------------|----------|-------------|
| Agent identity (SOUL) | `lifeline/SOUL.md` | Declarative identity, not just system prompt |
| Reflection system | `lifeline/REFLECTIONS/` | Post-task learning capture |
| 15 memory engine concepts | `lifeline/IDENTITY.md` | Aspirational memory architecture |
| Self-Improvement skill | `skills/self_improvement_skill/` | Automated learning loop |
| Tiered Memory skill | `skills/tiered_memory_skill/` | HOT/WARM/COLD lifecycle |
| Ontology skill | `skills/ontology_skill/` | Structured knowledge graph |
| Skill Stealer | `skills/skill_stealer_skill/` | Cross-platform skill porting |
| File Learner | `skills/file_learner_skill/` | Project pattern extraction |
| Setup wizard (TUI) | `tui/src/components/setup-wizard.tsx` | Guided first-run experience |
| Gogeta branding | `tui/` | Gold/corsair identity |

### Integration Opportunities

| Opportunity | Systems Involved | Benefit |
|-------------|-----------------|---------|
| Lifeline → Session Platform | lifeline/ + session | Auto-populate TIMELINE.md from session data |
| Lifeline → Reflection Engine | lifeline/ + agent | Automated post-task reflection |
| Skills → Context Engine | skills/ + context | Relevance-based skill injection |
| Skills → Tool Registry | skills/ + tools/ | Executable skills registered as tools |
| TUI → Event Bus | tui/ + events | Real-time UI updates from system events |
| TUI → Session Platform | tui/ + session | FTS5 search, crash recovery |
| Lifeline → Project Intelligence | lifeline/ + intelligence | Identity drives project docs |
| Tools → Cost Intelligence | tools/ + cost | Per-tool cost tracking |

---

## 6. Priority Recommendations

### Immediate (Phase 1-2)
1. **Audit the 15 memory engines** — They're currently aspirational. Either implement them as real memory providers or document them as architectural concepts.
2. **Consolidate skill registry** — Move unregistered skills (apple/, devops/, creative/, etc.) into `registry.json`.

### Phase 3-4 (Tool Platform + Events)
3. **Extend ToolRegistry for analytics** — Add usage counters, latency tracking, and cost attribution hooks.
4. **Add tool permissions** — Implement per-tool ACLs using the existing `permissions.py` as foundation.

### Phase 5-6 (Sessions + Context)
5. **Upgrade TUI session persistence** — Replace JSON files with SQLite backed by the Session Platform.
6. **Auto-populate Lifeline templates** — TIMELINE.md, WORLDSTATE.md, ENERGY.md should auto-update from system state.
7. **Connect skills to Context Engine** — Skills should be injected into context based on relevance scoring, not loaded unconditionally.

### Phase 7+ (Agent Evolution)
8. **Upgrade Self-Improvement skill to platform service** — The learning loop should be a core capability, not a skill the agent has to invoke.
9. **Connect Lifeline to Project Intelligence** — SOUL identity should drive project documentation.
10. **Implement Tiered Memory as a memory provider** — The HOT/WARM/COLD concept should become a real memory backend.
