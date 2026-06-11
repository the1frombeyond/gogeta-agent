---
name: gog
description: Unified Google Services skill for Gmail, Calendar, Drive, Contacts, Sheets, and Docs.
version: 1.0.0
---

# GOG - Google Services Skill

This skill provides JARVIS with full access to your Google Workspace environment.

## Setup
1. Provide your `client_secret.json` from the Google Cloud Console.
2. Run `gog auth credentials /path/to/json`.
3. Add your account: `gog auth add you@gmail.com --services all`.

## Instructions
- **Gmail**: Use `gmail search` or `gmail send`.
- **Calendar**: Use `calendar events` to list or create schedules.
- **Drive**: Use `drive search` to find documents.
- **Sheets**: Use `sheets get`, `sheets update`, or `sheets append` for spreadsheet data.
- **Docs**: Use `docs cat` or `docs export`.

## Safety
- Always confirm before sending emails or creating/deleting calendar events.
- Sheets updates should be double-checked by the Critic MCP.
