---
name: tiered_memory
description: Adaptive, multi-tiered memory system that manages HOT, WARM, and COLD storage for continuous learning.
version: 1.0.0
---

# Tiered Memory Skill

This skill allows JARVIS to manage your preferences and learnings across different levels of urgency and relevance.

## Storage Tiers
1. **HOT (`memory.md`)**: Always loaded into context. For your core global preferences (max 100 lines).
2. **WARM (`projects/`, `domains/`)**: Loaded when the task area matches. For project-specific rules (max 200 lines).
3. **COLD (`archive/`)**: Archived patterns that are no longer frequently used but kept for history.

## Lifecycle Rules
- **Promotion**: If a pattern is used successfully 3 times in 7 days, it is promoted to **HOT**.
- **Demotion**: If a pattern is unused for 30 days, it is moved to **WARM**.
- **Archiving**: If a pattern is unused for 90 days, it is moved to **COLD**.

## Self-Reflection
After every major task, JARVIS should log:
- **CONTEXT**: What was the task?
- **REFLECTION**: What went well or could be better?
- **LESSON**: What should be changed in the memory system?

## Files
- `.mark/self-improving/memory.md`
- `.mark/self-improving/corrections.md`
- `.mark/self-improving/index.md`
