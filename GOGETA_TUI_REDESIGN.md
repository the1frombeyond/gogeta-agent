# TUI Preservation + Gogeta Rebranding Directive

You are **NOT building a new TUI from scratch**.

You are **rewriting the existing Gogeta TUI into the Gogeta TUI**.

The current Gogeta setup wizard, keyboard navigation system, onboarding flow, and terminal UX are valuable assets and must be preserved where possible.

---

# Primary Goal

Transform:

```text
Gogeta Agent
```

into

```text
Gogeta 3.0
```

while preserving:

```text
UX
Keyboard Flow
Setup Experience
Terminal Feel
Cross-platform Support
```

and improving architecture underneath.

---

# TUI Rewrite Rules

Do NOT create an entirely new TUI.

Instead:

1. Audit existing Gogeta TUI
2. Audit previous Gogeta TUI
3. Merge best features of both
4. Rewrite architecture
5. Preserve user experience

Goal:

```text
Same quality users already like
+
Cleaner architecture
+
Modern design
+
Gogeta branding
```

---

# Setup Wizard Requirements

Reuse the existing keyboard-driven wizard design.

Preserve:

```text
Arrow Keys
j / k navigation
Space toggle
Enter confirm
a = toggle all
Select All row
```

Preserve visual style:

```text
> ● [ 1] Web Search
  ○ [ 2] File System
```

Preserve:

```text
N/M selected
```

footer.

---

# Cross Platform Input

Maintain dual implementations:

Unix:

```python
termios
tty
stdin.read()
```

Windows:

```python
msvcrt.getch()
```

Do NOT force a shared raw-input layer.

Keep separate implementations.

---

# TUI Modernization

Upgrade appearance to be comparable to:

```text
Claude Code
Gemini CLI
Warp
Ghostty
```

without adding unnecessary complexity.

Add:

### Better Layout

```text
Header
Status Bar
Context Bar
Main View
Footer
```

### Live Status

Show:

```text
Current Model
Current Provider
Token Usage
Session Cost
Agent State
```

### Agent Visibility

Display:

```text
Architect
Research
Coding
Testing
Security
Documentation
```

status when active.

### Delegation View

Show:

```text
Parent Agent
Child Agents
Task Progress
Completion %
```

---

# Project Intelligence Integration

Display live information from:

```text
project.md
tasks.md
architecture.md
decision_log.md
```

inside the TUI.

Allow:

```text
View Current Goal
View Active Tasks
View Recent Decisions
View Architecture Status
```

without leaving terminal.

---

# Lifeline Integration

Add dedicated Lifeline view.

Display:

```text
SOUL.md
TIMELINE.md
MEMORIES.md
MISSIONS.md
WORLDSTATE.md
```

Allow browsing from TUI.

---

# Genome Integration

Add Genome dashboard.

Display:

```text
Learned Workflows
Workflow Confidence
Discovered Patterns
Evolved Skills
Failure Lessons
```

Use:

```text
workflow_graph.json
genome.json
genome.md
```

as sources.

---

# Session View

Add:

```text
Recent Sessions
Search Sessions
Resume Session
Export Session
```

similar to Gogeta session browser.

---

# Cost Intelligence View

Display:

```text
Provider
Model
Tokens
Latency
Cost
Budget
```

Live updating from:

```text
gateway/cost_intelligence.py
```

---

# Event Bus Integration

The TUI must subscribe to:

```text
core/events/
```

and update in real time.

Display event stream:

```text
TOOL_STARTED
TOOL_FINISHED
TOOL_FAILED
SESSION_STARTED
SESSION_ENDED
PROVIDER_SELECTED
PROJECT_UPDATED
```

---

# WhatsApp Integration

Preserve QR onboarding flow.

Improve:

```text
QR rendering
Connection feedback
Session persistence
Reconnect status
```

Store sessions in:

```text
~/.GOGETA/sessions/
```

not Gogeta locations.

---

# Full Gogeta → Gogeta Rename

Rename EVERYTHING.

Not only folders.

Also:

## Classes

```text
GsaCLI
GsaAgent
GsaGateway
GsaState
GsaSession
```

become:

```text
GsaCLI
GsaAgent
GsaGateway
GsaState
GsaSession
```

---

## Variables

Rename:

```text
gogeta_home
gogeta_config
gogeta_state
gogeta_session
```

to:

```text
gogeta_home
gogeta_config
gogeta_state
gogeta_session
```

---

## Environment Variables

Rename:

```text
GOGETA_HOME
GOGETA_CONFIG
GOGETA_PROFILE
```

to:

```text
GOGETA_HOME
GOGETA_CONFIG
GOGETA_PROFILE
```

Maintain compatibility shims.

---

## Config Files

Rename:

```text
gogeta.yaml
```

to:

```text
gogeta.yaml
```

---

## User Facing Text

Remove:

```text
Gogeta
Nous Research
Gogeta Agent
```

from:

```text
Help Screens
CLI Output
Logs
TUI
Docs
Comments
README
```

Replace with:

```text
Gogeta
Gogeta 3.0
```

---

# Research Requirement

Before modifying any subsystem:

Research current best practices for:

```text
Terminal UIs
Coding Agents
Session Management
Context Management
Agent Architectures
Model Routing
Provider Gateways
Tool Systems
```

Compare against:

```text
Claude Code
Gemini CLI
Aider
OpenCode
Cursor
Cline
Roo Code
```

If existing implementation is outdated:

```text
Upgrade it.
```

If implementation is still strong:

```text
Keep it.
```

---

# Preservation Rule

For every Gogeta subsystem:

```text
Audit
Preserve
Improve
Integrate
```

For every Gogeta subsystem:

```text
Keep
Upgrade
Expand
```

Avoid:

```text
Delete
Rewrite blindly
Replace working systems
```

unless a written migration document explains why.

---

# Final Objective

Build:

```text
Best of Gogeta
+
Best of Existing Gogeta
+
Modern Agent Architecture
+
Modern CLI/TUI UX
+
Full Gogeta Identity
=
Gogeta 3.0
```

The goal is not a new project.

The goal is a complete evolution of Gogeta into Gogeta while preserving everything users already love. # GOGETA-SPACE TUI REDESIGN DIRECTIVE

You are redesigning the existing Gogeta TUI into the new Gogeta TUI.

This is NOT a rewrite from scratch.

This is NOT a new TUI.

This is a modernization and rebrand of the existing working Gogeta interface.

Study the current implementation first.

Preserve working functionality.

Preserve keyboard shortcuts.

Preserve command handling.

Preserve session handling.

Preserve provider integration.

Only redesign the presentation layer and improve UX where appropriate.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIMARY BRANDING

Replace Gogeta branding with:

GOGETA-SPACE

Use this exact banner:

 ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗       ███████╗██████╗  █████╗  ██████╗███████╗
██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗      ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║█████╗███████╗██████╔╝███████║██║     █████╗
██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║╚════╝╚════██║██╔═══╝ ██╔══██║██║     ██╔══╝
╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║      ███████║██║     ██║  ██║╚██████╗███████╗
 ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝      ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝

Replace:

Gogeta Agent
Gogeta
gogeta
GOGETA
gogeta-agent
gogeta_agent

with:

GOGETA-SPACE
Gogeta
gogeta

throughout the TUI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEEP

Keep:

Model display

Example:

Model: gemini-2.5-pro

Keep:

Session display

Example:

Session: Build Gogeta 3.0

Keep:

Home directory display

Example:

Path: C:\Users\the1frombeyond

Keep:

Bottom command input

Keep:

Full screen terminal experience

Keep:

Existing rendering architecture if stable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMOVE COMPLETELY

Delete:

Available Skills

Delete:

77 skills

Delete:

Skill categories:

autonomous-ai-agents
creative
data-science
devops
github
research
media
productivity
mlops
software-development
and all other category listings

Delete:

Available Tools

Delete:

30 tools

Delete:

Tool registry dump

Delete:

(and 22 more toolsets...)

Delete:

Any giant startup inventory lists

The startup screen should not be a catalog.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REPLACE CENTER PANEL

Replace all tool/skill listings with a live intelligence dashboard.

Show:

╭──────────────── Session Summary ────────────────╮
│ Goal                                            │
│ Build Gogeta 3.0                                │
│                                                  │
│ Current Task                                    │
│ Active migration task                           │
│                                                  │
│ Progress                                        │
│ ████████████░░░░░░░░                            │
│                                                  │
│ Files Modified                                  │
│ Dynamic                                          │
│                                                  │
│ Tests                                            │
│ Dynamic                                          │
│                                                  │
│ Cost                                             │
│ Dynamic                                          │
│                                                  │
│ Context                                          │
│ Dynamic                                          │
│                                                  │
│ Genome                                           │
│ Learning                                          │
╰──────────────────────────────────────────────────╯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADD RECENT ACTIVITY PANEL

Example:

╭──────────────── Recent Activity ────────────────╮
│ ✓ Event Bus Built                               │
│ ✓ Project Intelligence Built                    │
│ ✓ Lifeline Built                                │
│ ✓ Genome Built                                  │
│ ✓ Session Watchers Extracted                    │
│ ✓ Architecture Engine Active                    │
│ → Current Task                                  │
╰──────────────────────────────────────────────────╯

Populate from:

Event Bus
Project Intelligence
project.md
tasks.md
decision_log.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADD ACTIVE SYSTEMS PANEL

Example:

╭──────────────── Active Systems ────────────────╮
│ Architecture Engine      ✓                     │
│ Event Bus                ✓                     │
│ Genome                   ✓                     │
│ Lifeline                 ✓                     │
│ Cost Intelligence        ✓                     │
│ Session Manager          ✓                     │
│ Project Intelligence     ✓                     │
│ Memory System            ✓                     │
╰─────────────────────────────────────────────────╯

System status should be real.

Not hardcoded.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HEADER STATUS BAR

Display:

Model
Provider
Session
Cost
Tokens
Genome
Memory
Context
Path

Example:

╭──────────────── GOGETA-SPACE ────────────────╮
│ Model    : gemini-2.5-pro                    │
│ Session  : Build Gogeta 3.0                  │
│ Cost     : $0.04                             │
│ Tokens   : 31k                               │
│ Genome   : Learning                          │
│ Path     : C:\Users\the1frombeyond           │
╰──────────────────────────────────────────────╯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEME

Primary:
Gold

Secondary:
White

Success:
Green

Warnings:
Orange

Errors:
Red

Use ANSI colors.

Keep terminal compatibility.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESEARCH REQUIREMENT

Before making UX changes:

Research:

Claude Code
Gemini CLI
OpenCode
Aider
Cursor Agent
Warp AI

Study:

session displays
status bars
cost displays
context indicators
command palettes
slash commands
keyboard workflows

Integrate the best ideas.

Do NOT blindly copy.

Adapt them to Gogeta.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOGETA SYSTEM INTEGRATION

Integrate:

Architecture Engine
Event Bus
Project Intelligence
Genome
Lifeline
Cost Intelligence
Session System
Memory System

The TUI should expose these systems visually.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MIGRATION RULE

Do NOT build a second TUI.

Do NOT create a parallel interface.

Do NOT replace working Gogeta functionality.

Audit first.

Preserve functionality.

Modernize architecture.

Rebrand to Gogeta.

Improve UX.

Result:

Existing Gogeta TUI
+
Existing Gogeta Systems
+
Modern AI Agent UX

=

GOGETA-SPACE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADDITIONAL REQUIREMENTS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. NO NEW TUI FRAMEWORK

Do not replace the existing Gogeta TUI framework.

Do not migrate to:

- Textual
- Rich Live
- Prompt Toolkit rewrites
- BubbleTea
- New rendering systems

unless there is a documented architectural reason.

Reuse existing rendering code where possible.

Modernize, do not replace.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. PRESERVE STARTUP SPEED

The redesigned TUI must start as fast or faster than the current Gogeta TUI.

Do not add expensive startup scans.

Do not enumerate all tools, skills, genome entries, memories, or sessions during startup.

Load heavy data lazily.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. ADD COMMAND PALETTE

Inspired by Claude Code and Cursor:

Add a lightweight command palette.

Examples:

/help
/status
/genome
/lifeline
/project
/tasks
/sessions
/cost
/memory
/models

The TUI should surface system information through commands instead of giant startup panels.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. ADD COLLAPSIBLE PANELS

Instead of static screens:

Session Summary
Recent Activity
Active Systems
Genome
Lifeline

should be collapsible.

Keyboard:

TAB = next panel
SHIFT+TAB = previous panel
SPACE = collapse/expand

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. ADD EVENT STREAM VIEW

You already built an Event Bus.

Use it.

Recent Events

✓ TOOL_FINISHED
✓ PROJECT_UPDATED
✓ GENOME_LEARNED
✓ SESSION_SAVED
✓ MEMORY_STORED
✓ REFLECTION_CREATED

This will make Gogeta feel alive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. SHOW REAL CONTEXT STATE

You built ContextBuilder and SessionSummarizer.

Expose them.

Context:
87% used

Compression:
Active

Anchored Summary:
Loaded

Last Compression:
12m ago

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. SHOW GENOME PROGRESS

Instead of just:

Genome: Learning

show:

Genome

Workflows: 14
Patterns: 62
Skills: 9
Confidence: 84%
Status: Learning

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. SHOW LIFELINE PROGRESS

Lifeline

Memories: 47
Reflections: 22
Missions: 4
Failures Learned: 11

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. FORCE FULL GOGETA → GOGETA AUDIT

Before any UI work:

Generate:

docs/identity/

gogeta_references.md
rename_plan.md
branding_audit.md

Find every remaining:

Gogeta
gogeta
GOGETA
GsaAgent
GsaCLI
gogeta_agent
gogeta_cli

reference in the repository.

Replace or document it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. TUI SUCCESS TEST

Add a measurable goal:

When Gogeta launches:

The user should immediately understand:

1. What model is active
2. What task is active
3. What the agent is doing
4. What systems are running
5. What the project status is
6. What the genome has learned
7. What the lifeline remembers
8. How much the session costs

without typing a command.

That final requirement is important because it transforms the UI from a tool catalog into an agent cockpit, which fits everything you've built in Phases 1–12.
