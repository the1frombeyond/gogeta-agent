---
name: agent_browser
description: Deterministic browser automation skill using reference-based interactions (@e1, @e2) and multi-session isolation.
version: 1.0.0
---

# Agent Browser Skill

This skill allows JARVIS to perform high-performance, multi-step browser workflows with deterministic element selection.

## Core Workflow
1. **Navigate**: `open <url>`
2. **Snapshot**: `snapshot -i --json` (Generates `@e1`, `@e2` references).
3. **Interact**: Use refs to `click`, `fill`, or `hover`.
4. **Iterate**: Re-snapshot after page changes.

## Commands
- `open <url>`: Navigate to a site.
- `snapshot -i --json`: Get interactive element map.
- `click @ref`: Click element by reference ID.
- `fill @ref "text"`: Input text into a field.
- `state save/load`: Persist cookies and storage.
- `--session <name>`: Run in an isolated browser context.

## Best Practices
- Always use the `-i` flag to focus on interactive elements.
- Always use `--json` for structured data extraction.
- Use `wait --load networkidle` for stability in complex SPAs.
- Use sessions to isolate different user roles (e.g., admin vs user).

## Files
- `agent_browser.py`: Core Playwright execution engine.
