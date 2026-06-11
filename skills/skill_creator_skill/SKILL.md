---
name: skill_creator
description: Comprehensive guidance and tools for creating, validating, and packaging standardized Agent Skills for JARVIS.
version: 1.0.0
---

# Skill Creator Agent Skill

This skill provides the blueprints and automation tools for expanding JARVIS's intelligence with new, high-quality Agent Skills.

## Core Principles
1. **Concise is Key**: Keep `SKILL.md` body under 500 lines. Focus on context that Claude doesn't already have.
2. **Progressive Disclosure**: Only name and description are loaded at discovery. Detailed instructions load only upon activation.
3. **No Clutter**: Avoid auxiliary files like `README.md` or `CHANGELOG.md` within the skill folder.

## Anatomy of a Skill
- `SKILL.md`: Mandatory metadata (YAML) and procedural instructions.
- `scripts/`: Deterministic code (Python/Bash) for repetitive tasks.
- `references/`: Detailed documentation, schemas, and API specs.
- `assets/`: Templates, images, and boilerplate code.

## Workflow
1. **Init**: Run `scripts/init_skill.py <name>` to bootstrap a new skill.
2. **Implement**: Write `SKILL.md` and add resources.
3. **Validate**: Check metadata and structure.
4. **Package**: Run `scripts/package_skill.py <folder>` to create a `.skill` distribution.

## Tools
- `skills/skill_creator_skill/scripts/init_skill.py`
- `skills/skill_creator_skill/scripts/package_skill.py`
