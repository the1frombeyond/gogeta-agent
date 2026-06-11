---
name: skill_stealer
description: Autonomous skill acquisition system that discovers and imports capabilities from other AI platforms like Claude Code, Antigravity, and OpenClaw.
version: 1.0.0
---

# Skill Stealer Agent Skill

This skill allows JARVIS to expand his capabilities by "stealing" (importing) skills from other AI ecosystems.

## Instructions
1. **Discover**: Scan known directories for other AI agents (e.g., `~/.claude`, `~/.openclaw`).
2. **Analyze**: Read the `SKILL.md` or equivalent metadata from discovered skills.
3. **Ingest**: Copy the skill folder into `skills/` and ensure it has a valid `SKILL.md` matching the JARVIS standard.
4. **Refactor**: If necessary, update script paths or environment variable requirements to match JARVIS's architecture.

## Target Directories
- `~/.claude/skills/`
- `~/.openclaw/skills/`
- `~/.antigravity/skills/`

## Safety
- Always ask for permission before importing a new skill.
- Scan scripts for potentially malicious code before ingestion.
