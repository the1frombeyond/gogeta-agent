# Langfuse Observability Plugin

This plugin ships bundled with Gogeta but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
gogeta tools  # → Langfuse Observability

# Manual
pip install langfuse
gogeta plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.gogeta/.env` (or via `gogeta tools`):

```bash
GOGETA_LANGFUSE_PUBLIC_KEY=pk-lf-...
GOGETA_LANGFUSE_SECRET_KEY=sk-lf-...
GOGETA_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
gogeta plugins list                 # observability/langfuse should show "enabled"
gogeta chat -q "hello"              # then check Langfuse for a "Gogeta turn" trace
```

## Optional tuning

```bash
GOGETA_LANGFUSE_ENV=production       # environment tag
GOGETA_LANGFUSE_RELEASE=v1.0.0       # release tag
GOGETA_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
GOGETA_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
GOGETA_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
gogeta plugins disable observability/langfuse
```
