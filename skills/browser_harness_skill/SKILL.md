---
name: browser_harness
description: Advanced CDP-based browser control with self-improving helpers and site-specific domain skills.
version: 1.0.0
---

# Browser Harness Skill

This skill allows JARVIS to connect directly to your real browser and improve his own navigation logic as he learns new websites.

## Workflow
1. Connect via CDP to `localhost:9222`.
2. If a complex interaction is needed, check `agent-workspace/agent_helpers.py`.
3. If a helper is missing, write it.
4. After successfully automating a new site, create a domain skill in `agent-workspace/domain-skills/`.

## Key Files
- `src/browser_harness/core.py`: The CDP connection engine.
- `agent-workspace/agent_helpers.py`: Your custom browser helpers.
