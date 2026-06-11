---
name: web_search
description: High-speed web search capability for finding real-time information, news, and facts using local intelligence.
version: 1.0.0
---

# Web Search Skill

This skill allows JARVIS to quickly find information on the internet to answer questions about current events, facts, or technical details.

## Instructions
1. When the user asks a question about something current or unknown, trigger this skill.
2. Use the `search` function to query Google or DuckDuckGo.
3. Extract the top snippets and provide a concise answer.
4. If the user wants a deep dive, transition to the `browser_use` skill for full page extraction.

## Performance
- Focuses on speed and snippet extraction.
- Minimal bandwidth usage compared to full browsing.
