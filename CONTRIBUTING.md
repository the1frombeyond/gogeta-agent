# Contributing to Gogeta 3.0

Thank you for your interest in Gogeta — the self-improving AI agent. We welcome contributions of all kinds: bug fixes, features, skills, plugins, documentation, and more.

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
All participants are expected to uphold this code. Report unacceptable behavior in the [Discord](https://discord.gg/NousResearch).

---

## Getting Started

### System Requirements

| Requirement | Version |
|---|---|
| **Python** | >=3.11, <3.14 |
| **Node.js** | >=18 (needed for browser tools, TUI, WhatsApp bridge) |
| **Git** | with `git-lfs` |
| **uv** | Fast Python package manager ([install](https://docs.astral.sh/uv/)) |

### Clone & Install

```bash
git clone https://github.com/NousResearch/gogeta-agent.git
cd gogeta-agent

# Install with all extras (development + all optional dependencies)
uv sync --group dev --group all

# Or with pip:
# pip install -e ".[all,dev]"

# Browser automation dependencies (optional)
npm install
```

### Verify Installation

```bash
# Check the CLI works
gogeta --help

# Run diagnostics
gogeta doctor

# Quick test
gogeta chat -q "Hello" --quiet
```

### Configure for Development

```bash
mkdir -p ~/.gogeta/{cron,sessions,logs,memories,skills}
cp cli-config.yaml.example ~/.gogeta/config.yaml
touch ~/.gogeta/.env
# Add at least one LLM provider key:
echo "OPENROUTER_API_KEY=your_key" >> ~/.gogeta/.env
```

---

## Development Workflow

### Branch Naming

```
fix/what-you-fix         # Bug fixes
feat/what-you-add        # New features
docs/what-you-document   # Documentation
test/what-you-test       # Tests
refactor/what-you-clean  # Code restructuring
```

### Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Type | When |
|---|---|
| `fix` | Bug fixes |
| `feat` | New features |
| `docs` | Documentation |
| `test` | Tests |
| `refactor` | Code restructuring (no behavior change) |
| `chore` | Build, CI, dependency updates |

Scopes: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `tui`, `cron`, `kanban`, `plugins`, `providers`, `security`, etc.

Examples:
```
fix(cli): prevent crash when model config is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
test(tools): add unit tests for file_operations
```

### PR Process

1. **Keep PRs focused** — one logical change per PR
2. **Run tests** before submitting: `scripts/run_tests.sh`
3. **Test manually** — exercise the code path you changed
4. **Check cross-platform** — consider macOS, Linux, and Windows/WSL2
5. **Fill the PR template** — include what changed, why, and how to test
6. **Link related issues** with `Closes #123`, `Fixes #456`, or `Relates to #789`

PR review checklist: your code must follow project standards, pass tests, generate no new warnings, include documentation where needed, and not introduce breaking changes without documentation.

---

## Coding Standards

### Python

- Follow **PEP 8** with practical exceptions (line length is not strictly enforced)
- Use **type hints** for all function signatures
- Use `pathlib.Path` for filesystem paths — never hardcode `~/.gogeta`
- Use `get_gogeta_home()` from `gogeta_constants` instead of `Path.home() / ".gogeta"`
- Use `display_gogeta_home()` for user-facing path messages
- Catch specific exceptions — log with `logger.warning()`/`.error()` and `exc_info=True`
- Never assume Unix — all file I/O, process management, and shell calls must be cross-platform
- No `os.kill(pid, 0)` for liveness checks — use `psutil.pid_exists()`
- All handlers MUST return a JSON string

### TypeScript

Applies to `ui-tui/`, `apps/desktop/`, `web/`, and `website/`:

- Prefer small **nanostores** over component state for shared/reused state
- Use `useStore` for rendering from atoms, `$atom.get()` for non-rendering reads
- Keep route roots thin — compose routes and shell, don't make them controllers
- **No monolithic hooks** — one hook, one narrow job
- Prefer `interfaces` for public props and shared object shapes
- Extend React primitives for props: `React.ComponentProps<'button'>`, `Omit<...>`, `Pick<...>`
- Table-driven beats condition ladders
- `src/app` owns routes/pages; `src/store` owns shared atoms; `src/lib` owns pure helpers
- Async handlers: `onClick={() => void save()}`
- Format with **prettier**, lint with **eslint**, type-check with `tsc --noEmit`
- UI-TUI dev: `cd ui-tui && npm run dev` (watch mode)

### Testing Requirements

- All new code must include tests
- Tests must not write to `~/.gogeta/` — use the `_isolate_gogeta_home` fixture
- Use `monkeypatch` and `tmp_path` for env-var and filesystem dependencies
- No live network calls in unit tests
- **No change-detector tests** — test behavior and invariants, not data snapshots

---

## Testing Guide

### Run Tests

Always use the wrapper script for CI parity:

```bash
scripts/run_tests.sh                                     # Full suite
scripts/run_tests.sh tests/gateway/                      # One directory
scripts/run_tests.sh tests/agent/test_foo.py::test_x     # One test
scripts/run_tests.sh -v --tb=long                         # Pass-through flags
scripts/run_tests.sh --no-isolate tests/foo/              # Disable isolation (debugging)
```

The wrapper enforces hermetic environment: API keys unset, temp HOME, UTC timezone, `C.UTF-8` locale, and `-n auto` xdist workers.

### Writing Tests

- Framework: **pytest** + **unittest.mock**
- Tests run in isolated subprocesses (via `tests/_isolate_plugin.py`) — no state leakage
- Each test has a 30-second timeout (`isolate_timeout`)
- Subprocess-per-test overhead is ~0.5–1.0s, amortized by xdist

```python
# Good — test behavior, not data snapshots
def test_catalog_plumbing():
    assert "gemini" in _PROVIDER_MODELS
    assert len(_PROVIDER_MODELS["gemini"]) >= 1

# Bad — change detector that breaks every release
# assert "gemini-2.5-pro" in _PROVIDER_MODELS["gemini"]
# assert len(_PROVIDER_MODELS["huggingface"]) == 8
```

Skill tests go in `tests/skills/test_<skill>_skill.py` — stdlib + pytest + `unittest.mock` only.

---

## Adding a New Tool

For most custom tools, use the **plugin route** instead of modifying core. Create `~/.gogeta/plugins/<name>/plugin.yaml` and `__init__.py` with `ctx.register_tool(...)`.

For core tools that should ship with the system, use the **2-file process**:

**File 1: `tools/your_tool.py`**

```python
import json
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": param})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")
    ),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**File 2: `toolsets.py`**

Add your tool name to `_GOGETA_CORE_TOOLS` or a new toolset in the `TOOLSETS` dict. Auto-discovery imports the tool automatically, but wiring into a toolset is a deliberate manual step — tools are only exposed to the agent if they appear in a toolset.

Rules:
- Path references in schemas must use `display_gogeta_home()`
- State files must use `get_gogeta_home()` for the base directory
- All handlers MUST return a JSON string

---

## Adding a New Plugin

### Plugin Structure

```
~/.gogeta/plugins/your-plugin/
├── plugin.yaml          # Metadata
└── __init__.py          # register(ctx) function
```

Or for bundled plugins: `plugins/your-plugin/` in the repo tree.

A plugin's `register(ctx)` can:
- Register lifecycle hooks: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`
- Register new tools via `ctx.register_tool(...)`
- Register CLI subcommands via `ctx.register_cli_command(...)`

**Important:** Plugins MUST NOT modify core files (`run_agent.py`, `cli.py`, `gateway/run.py`, `gogeta_cli/main.py`). If a plugin needs a new capability, expand the generic plugin surface (new hook, new ctx method).

### Memory Provider Plugins

New memory backends must ship as standalone plugin repos — the set of in-tree providers is closed. Implement the `MemoryProvider` ABC from `agent/memory_provider.py` (`sync_turn`, `prefetch`, `shutdown`, `post_setup`).

### Model Provider Plugins

Each provider ships as a plugin under `plugins/model-providers/<name>/`. Call `providers.register_provider(ProviderProfile(...))` at module load. User plugins override bundled ones (last-writer-wins).

---

## Adding a Configuration Option

### config.yaml (settings — timeouts, thresholds, feature flags, paths, display preferences)

1. Add the key to `DEFAULT_CONFIG` in `gogeta_cli/config.py`
2. Bump `_config_version` ONLY if you need to actively migrate existing user config (renaming keys, changing structure). Adding a new key to an existing section is automatic — no version bump needed.

### .env (SECRETS ONLY — API keys, tokens, passwords)

1. Add to `OPTIONAL_ENV_VARS` in `gogeta_cli/config.py` with metadata:
```python
"NEW_API_KEY": {
    "description": "What it's for",
    "prompt": "Display name shown during setup",
    "url": "https://...",
    "password": True,
    "category": "tool",  # "provider", "tool", "messaging", or "setting"
}
```

Non-secret settings belong in `config.yaml`, not `.env`.

### Config Loaders

| Loader | Used by | Location |
|--------|---------|----------|
| `load_cli_config()` | CLI mode | `cli.py` |
| `load_config()` | `gogeta tools`, `gogeta setup`, most subcommands | `gogeta_cli/config.py` |
| Direct YAML load | Gateway runtime | `gateway/run.py` + `gateway/config.py` |

If you add a key and the CLI sees it but the gateway doesn't (or vice versa), check `DEFAULT_CONFIG` coverage.

---

## Skills Contributions

### SKILL.md Standards (8 HARDLINE Rules)

Every new or modernized skill must meet these before merge:

1. **`description` ≤ 60 characters**, one sentence ending with a period. No marketing words ("powerful", "comprehensive", "seamless", "advanced"). Don't repeat the skill name.

2. **Tools referenced in SKILL.md prose must be native Gogeta tools or MCP servers.** Use backtick-named tools: `` `terminal` ``, `` `web_extract` ``, `` `read_file` ``, `` `patch` ``, `` `search_files` ``. Do NOT name shell utilities — `grep` → `search_files`, `cat`/`head`/`tail` → `read_file`, `sed`/`awk` → `patch`.

3. **`platforms:` gating audited against actual script imports.** Default: fix it cross-platform first — `tempfile.gettempdir()`, `pathlib.Path`, `psutil.pid_exists()`. Gate only when genuinely platform-bound.

4. **`author` credits the human contributor first.** "Jane Doe (jane-doe)" before "Gogeta Agent".

5. **Modern section order:** `# <Name> Skill` title → 2-3 sentence intro → `## When to Use` → `## Prerequisites` → `## How to Run` → `## Quick Reference` → `## Procedure` → `## Pitfalls` → `## Verification`. Target ~200 lines (complex) or ~100 lines (simple).

6. **Scripts in `scripts/`, references in `references/`, templates in `templates/`.** Ship helper scripts — don't expect the model to inline-write parsers every call.

7. **Tests at `tests/skills/test_<skill>_skill.py`** — stdlib + pytest + `unittest.mock` only. No live network calls.

8. **`.env.example` additions in a clearly delimited block.** Comment all values with `#`. Don't touch surrounding file.

### Skill vs Tool Decision

**Make it a Skill when:** the capability can be expressed as instructions + shell commands + existing tools; it wraps an external CLI or API; it doesn't need custom Python integration in the agent harness.

**Make it a Tool when:** it needs end-to-end integration with API keys, auth flows, and multi-component configuration; it needs custom processing logic that must execute precisely every time; it handles binary data, streaming, or real-time events.

### Bundled vs Optional

- **`skills/`** — broadly useful, ship with every install
- **`optional-skills/`** — official but niche/heavy, shipped but inactive by default
- **Skills Hub** — community-contributed, installed via `gogeta skills install`

---

## Documentation

- Documentation site: `website/` (Docusaurus)
- Architecture docs: `docs/`
- Developer guide: `AGENTS.md` (for AI coding assistants)
- Platform adapter docs: `docs/middleware/ADDING_A_PLATFORM.md`
- Model provider plugin docs: `website/docs/developer-guide/model-provider-plugin.md`

---

## Release Process

See `scripts/release.py` for the automated release pipeline. Version is defined in `pyproject.toml` (currently `0.16.0`). Releases follow semantic versioning.

---

## Getting Help

- **Discord**: [discord.gg/NousResearch](https://discord.gg/NousResearch) — questions, showcasing, sharing skills
- **GitHub Issues**: [github.com/NousResearch/gogeta-agent/issues](https://github.com/NousResearch/gogeta-agent/issues)
- **GitHub Discussions**: design proposals and architecture discussions
- **Docs**: [gogeta.ai/docs](https://gogeta.ai/docs/)
- **Skills Hub**: [agentskills.io](https://agentskills.io)
