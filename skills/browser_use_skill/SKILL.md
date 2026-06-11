---
name: browser_use
description: Autonomous web intelligence agent for searching, browsing, and extracting content safely using Playwright and Ollama.
version: 1.0.0
---

# Browser Use Agent Skill

This skill allows JARVIS to browse the web autonomously to gather information, research topics, and summarize content.

## Instructions
1. When asked to research a topic, use the `search_google` method.
2. When a specific URL is provided, use the `navigate` method.
3. Always extract clean text and provide a 5-point summary.
4. **SAFETY**: Never submit forms, login, or download files.

## Scripts
- `browser_use.py`: The core Playwright execution script.
