---
name: self_improvement
description: Continuous learning loop that captures insights, errors, and feature requests to evolve JARVIS's intelligence and reliability.
version: 1.0.0
---

# Self-Improvement Skill

This skill allows JARVIS to learn from his mistakes, capture user feedback, and improve his own system architecture over time.

## Workflow
1. **Detection**: Notice when a command fails, a user corrects a behavior, or a new feature is requested.
2. **Logging**: Record the event in `.learnings/` using the standard format:
   - `LEARNINGS.md`: For insights and corrections.
   - `ERRORS.md`: For command failures and technical issues.
   - `FEATURE_REQUESTS.md`: For tracking new capability requests.
3. **Promotion**: Move high-value, broadly applicable learnings to `AGENTS.md` (Workflows), `SOUL.md` (Personality), or `TOOLS.md` (Tool Gotchas).

## Formatting
- **ID**: `LRN-YYYYMMDD-XXX` or `ERR-YYYYMMDD-XXX`.
- **Priority**: low | medium | high | critical.
- **Status**: pending | resolved | promoted.

## Files
- `.learnings/LEARNINGS.md`
- `.learnings/ERRORS.md`
- `.learnings/FEATURE_REQUESTS.md`
