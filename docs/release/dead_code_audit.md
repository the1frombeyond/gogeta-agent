# Dead Code & Legacy Audit

Generated: 2026-06-11

---

## 1. `hermes_bootstrap.py` — Not Found

No file named `hermes_bootstrap.py` exists anywhere in the repository. No imports or references to `hermes_bootstrap` were found in any Python file. This is clean — there is no orphaned import.

---

## 2. Deprecated Features & Code

### Deprecated: `kanban daemon` subcommand
- **Location:** `gogeta_cli/kanban.py:1271-1277` and `gogeta_cli/kanban.py:4419`
- **Status:** Marked DEPRECATED — the kanban dispatcher now runs inside the gateway (`kanban.dispatch_in_gateway: true`). The standalone daemon CLI is kept for backward compatibility.
- **Recommendation:** Remove in next major version. Update docs to point to gateway-based dispatch.

### Deprecated: `auth.py` module header
- **Location:** `gogeta_cli/auth.py:1` (docstring)
- **Status:** Marked as "Deprecated: use 'gogeta model' or 'gogeta setup'"
- **Recommendation:** Confirm nothing imports it; if orphaned, remove.

### Deprecated: Environment variables `MESSAGING_CWD` and `TERMINAL_CWD`
- **Location:** `gateway/run.py:549-566`, `gogeta_cli/config.py:8495-8563`
- **Status:** Active deprecation warnings emitted at runtime. Canonical setting is `terminal.cwd` in `config.yaml`.
- **Recommendation:** Remove fallback handling in next major version.

### Deprecated: `tool_progress_overrides` config key
- **Location:** `gogeta_cli/config.py:2843`
- **Status:** Config key exists but is marked `# DEPRECATED`. Replaced by `display.tool_progress_*`.
- **Recommendation:** Remove key from `DEFAULT_CONFIG` and add a migration in `_migrate_config()`.

### Deprecated: `curator.auxiliary.*` config keys
- **Location:** `agent/curator.py:1644-1651`
- **Status:** Legacy config path. Migration code logs a deprecation warning.
- **Recommendation:** Remove legacy read path once migration is complete.

### Deprecated: `QQ_HOME_CHANNEL` env var
- **Location:** `gateway/config.py:1803`
- **Status:** Renamed — deprecation comment on the legacy name.
- **Recommendation:** Remove after verifying the rename has propagated.

### Deprecated: gh copilot extension (legacy)
- **Location:** `agent/copilot_acp_client.py:33-48,535`
- **Status:** Mocks/detection for the deprecated `gh copilot` extension. The new path is the Copilot ACP protocol.
- **Recommendation:** Retain during transition; remove when support for old extension is dropped.

### Deprecated: Certain Anthropic models (extended thinking)
- **Location:** `agent/anthropic_adapter.py:82`
- **Status:** Comment noting models where extended thinking is deprecated.
- **Recommendation:** Review and update model list per current Anthropic API docs.

---

## 3. Plugin Abandonment Assessment

### Model-provider plugins (27 total)
Every plugin under `plugins/model-providers/` consists of a single `__init__.py` file only. None have additional provider logic files. This is the **expected pattern** — model provider plugins register a `ProviderProfile` via `providers.register_provider()` at import time. They are not abandoned; they are intentionally minimal stubs.

### Platform plugins (all `__init__.py` only)
- `plugins/platforms/discord/` — one `__init__.py`
- `plugins/platforms/google_chat/` — one `__init__.py`
- `plugins/platforms/homeassistant/` — one `__init__.py`
- `plugins/platforms/irc/` — one `__init__.py`
- `plugins/platforms/line/` — one `__init__.py`
- `plugins/platforms/mattermost/` — one `__init__.py`
- `plugins/platforms/ntfy/` — one `__init__.py`
- `plugins/platforms/simplex/` — one `__init__.py`
- `plugins/platforms/teams/` — one `__init__.py`

**Status:** All are single-file stubs. This is intentional for the plugin discovery pattern. Not abandoned.

### Browser plugins (`plugins/browser/`)
- `browserbase/` — has `provider.py` + `__init__.py`
- `browser_use/` — has `provider.py` + `__init__.py`
- `firecrawl/` — has `provider.py` + `__init__.py`

**Status:** Active — all have real provider implementations.

### Image gen plugins (`plugins/image_gen/`)
All are `__init__.py`-only stubs: `fal/`, `krea/`, `openai/`, `openai-codex/`, `xai/`.

**Status:** Expected stub pattern. Not abandoned.

### Memory plugins (`plugins/memory/`)
Several are `__init__.py`-only: `byterover/`, `hindsight/`, `mem0/`, `openviking/`, `retaindb/`, `supermemory/`.

Fully implemented: `holographic/` (3 files), `honcho/` (3 files).

All are `__init__.py`-only stubs.
- **Note:** Project policy (May 2026) states the in-tree memory provider set is **closed** — no new providers will be added. Existing stubs may be abandoned or placeholder.
- **Recommendation:** Audit each stub to confirm it registers a working `MemoryProvider` (or remove it).

### Plugin with `_plugin_disabled()` gate
- **Location:** `plugins/security-guidance/__init__.py:70-194`
- **Status:** Has a `_plugin_disabled()` function. Not loaded by default — user must opt in.
- **Recommendation:** Document this opt-in status in the plugin readme. Consider removing if unused.

---

## 4. Duplicate Provider Patterns

### Model providers
The `providers/` directory (top-level) contains:
- `providers/base.py`
- `providers/__init__.py`

This is the **legacy provider discovery system**. The modern path is `plugins/model-providers/<name>/__init__.py`. `providers/__init__.py` contains `_discover_providers()` which scans both paths with legacy fallback:

> Scan order: 1) Bundled `<repo>/plugins/model-providers/<name>/` → 2) User `$GOGETA_HOME/plugins/model-providers/` → 3) Legacy `<repo>/providers/<name>.py`

**Recommendation:** Verify no active providers remain in the legacy `providers/` directory (only `base.py` and `__init__.py` remain — appears clean). Remove the legacy scan path in a future release.

### Web search plugins
9 parallel web search adapters exist: `brave_free`, `ddgs`, `exa`, `firecrawl`, `parallel`, `searxng`, `tavily`, `xai` + the built-in `web_search_provider.py`. This is intentional — they are interchangeable backends selected via config, not dead code.

---

## 5. Incomplete Work Markers (TODO/FIXME/HACK)

### High concentration files (most markers)

| File | Lines with markers | Notable patterns |
|---|---|---|
| `cli.py` | ~20 | TODOs on feature parity, edge cases |
| `run_agent.py` | ~17 | TODOs on budget handling, model routing |
| `agent/agent_runtime_helpers.py` | ~15 | TODOs on credential fallback paths |
| `agent/auxiliary_client.py` | ~3 | Large file with FIXME on rate limits |
| `agent/tool_executor.py` | ~7 | HACK comments on tool dispatch edge cases |
| `gateway/run.py` | ~14 | TODOs on platform-specific behavior |
| `gogeta_cli/kanban.py` | ~5 | Daemon deprecation TODOs |
| `agent/conversation_compression.py` | ~6 | Compression edge case TODOs |
| `agent/lsp/manager.py` | ~23 | LSP lifecycle/workaround TODOs |
| `agent/conversation_loop.py` | ~12 | Session management TODOs |
| `acp_adapter/tools.py` | ~15 | ACP protocol edge cases |
| `gateway/platforms/yuanbao.py` | ~7 | Platform-specific workarounds |
| `gogeta_cli/auth.py` | ~5 | Auth flow TODOs |

**Key findings requiring attention:**

- `gogeta_cli/providers.py` — contains commented-out provider entries (legacy model lists)
- `model_tools.py:553,556` — FIXME related to tool discovery
- `agent/jiter_preload.py:8` — HACK comment for import order workaround
- `agent/process_bootstrap.py:11,64` — TODOs on process lifecycle
- `gogeta_cli/codex_runtime_plugin_migration.py:993,1003` — migration TODOs for Codex plugin migration
- `agent/display.py:949-975` — multiple HACKs for terminal width/rendering

**Recommendation:** Review each TODO/FIXME/HACK. Prioritize security-related ones (marked FIXME in discretion checks, credential handling).

---

## 6. Empty or Minimal `__init__.py` Files

44 `__init__.py` files found with ≤3 lines of content. Most are in test directories (follows standard Python test package convention). Notable non-test ones:

| File | Status |
|---|---|
| `acp_adapter/__init__.py` | Minimal — expected for a package init |
| `plugins/__init__.py` | Empty — expected for plugin discovery |
| `plugins/platforms/{discord,google_chat,homeassistant,irc,line,mattermost,ntfy,simplex,teams}/__init__.py` | Empty — plugin stubs (see section 3) |
| `gateway/builtin_hooks/__init__.py` | Empty — documented as extension point (no hooks shipped) |
| `gateway/watchers/__init__.py` | Minimal — package init |
| `tui_gateway/__init__.py` | Minimal — package init |

**All are intentional.** No action needed.

---

## 7. Legacy / Migration Directories

### `docs/migration/extractions/`
Contains a single file: `kanban_extraction.md`.

**Status:** Appears to be a design document from extracting kanban into a standalone module. Not code — purely documentation. Consider moving to `docs/archive/` if no longer actively referenced.

### No `legacy/` directory
A top-level `legacy/` directory does not exist.

### `optional-skills/migration/`
Contains `openclaw-migration/scripts/openclaw_to_gogeta.py`.

**Status:** One-shot migration script for converting OpenClaw skills. Keep as reference for users migrating from OpenClaw.

---

## Summary

| Category | Items Found | Action Needed |
|---|---|---|
| Orphaned imports | None | — |
| Deprecated features | ~8 items | Remove in next major version |
| Abandoned plugin stubs | Possibly several memory plugins | Audit for registration logic |
| Duplicate provider systems | Legacy `providers/` + modern `plugins/model-providers/` | Remove legacy scan path |
| TODO/FIXME/HACK | ~150+ markers across files | Prioritize security-critical ones |
| Empty `__init__.py` | 44 total, all intentional | — |
| Migration/legacy dirs | 2 (docs + optional-skills) | Keep as-is |
