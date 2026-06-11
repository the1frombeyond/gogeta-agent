---
name: file_learner
description: Analyzes the user's workspace files to extract coding patterns, project structures, and styles, saving them into JARVIS's self-improvement memory.
version: 1.0.0
---

# File Learner Skill

This skill allows JARVIS to continuously better itself by learning from the files and code you write. It extracts patterns, preferred libraries, naming conventions, and project structures, then injects them directly into JARVIS's Tiered Memory (`.mark/self-improving/`).

## Core Capabilities
- **Style Extraction**: Reads source code to learn your preferred indentations, quoting styles, and architectural patterns.
- **Dependency Tracking**: Analyzes `requirements.txt`, `package.json`, etc., to understand your tech stack.
- **Memory Integration**: Automatically writes learned patterns into the WARM memory (`.mark/self-improving/projects/` or `domains/`).

## How to Use
To trigger this skill, ask JARVIS to:
- "Scan my project and learn my coding style."
- "Analyze this file and remember how I handle errors."

**Command Usage:**
`python skills/file_learner_skill/file_learner.py scan <directory_or_file>`

## Where Knowledge Goes
- Extracted domain knowledge goes to `.mark/self-improving/domains/<lang>.md`
- Project-specific quirks go to `.mark/self-improving/projects/<project>.md`
