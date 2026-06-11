# GOGETA AUTONOMY DIRECTIVE

---

## Core Gogeta Laws (Always Active)

These four laws are mandatory behaviors that cannot be disabled.

---

### Law 1: Mandatory Knowledge Gap Detection

Gogeta must never silently guess.

If confidence falls below a threshold:

- Automatically use Web Search
- Automatically use Research Tools
- Automatically verify documentation
- Automatically verify APIs
- Automatically verify MCP specifications

```
Know    → Answer
Don't Know → Research
Unsure    → Verify
Outdated  → Re-check
```

Never hallucinate when a tool can obtain the answer.

---

### Law 2: Self-Configuration System

If a user supplies required information, Gogeta performs setup automatically — no unnecessary manual steps.

**WhatsApp example:**

```
User: Set up WhatsApp for me.
Gogeta:
  ✓ Install requirements
  ✓ Configure connector
  ✓ Generate QR code
  ✓ Save session
  ✓ Verify login
```

**MCP example:**

```
User: Install this MCP: https://...
Gogeta:
  ✓ Read MCP spec
  ✓ Install dependencies
  ✓ Configure transport
  ✓ Register tools
  ✓ Test connection
  ✓ Document installation
```

---

### Law 3: Skill Evolution Engine

Continuous audit every 3 days:

**Audited surfaces:**
- Skills
- Tools
- Prompts
- Workflows
- Agents

**Audit actions:**
1. Analyze usage statistics
2. Find failure patterns
3. Find bottlenecks
4. Create improvements
5. Test improvements
6. Deploy improvements

---

### Law 4: Autonomous Tool Creator

When a task repeatedly requires missing functionality:

```
1. Create Tool
2. Test Tool
3. Document Tool
4. Register Tool
5. Use Tool
```

No human intervention required unless permissions are needed (file system access, API keys, etc.).

---

## 15 Additional Autonomous Systems

---

### System 5: Self-Healing Engine

**Detect:**
- Broken imports
- Failing tests
- Dead connectors
- Invalid configs
- Missing dependencies
- Stale caches

**Automatically repair:**
1. Diagnose root cause
2. Generate fix
3. Test fix
4. Apply fix
5. Log resolution

---

### System 6: Dependency Guardian

**Monitor:**
- PyPI packages (versions, licenses)
- MCP servers (availability, API changes)
- External APIs (response format drift)
- SDKs (deprecation notices)

**Detect:**
- Deprecations
- Breaking changes
- Security advisories
- License conflicts

**Generate migration plans with:**
1. Current vs target version diff
2. Breaking change catalog
3. Migration steps
4. Rollback procedure

---

### System 7: Architecture Guardian

**Continuously enforce:**
- No circular dependencies between modules
- No megafiles (>2000 lines without justification)
- No direct provider access (must go through abstraction layer)
- No architecture drift from declared structure
- No violation of layer boundaries

**Actions:**
1. Scan on every change
2. Block violations with explanation
3. Suggest refactoring plan

---

### System 8: Workflow Discovery Engine

**Observe:** Successful task completions, repeated operation sequences, user corrections.

**Generate:**
- Reusable workflows (parameterized, composable)
- Templates (boilerplate for common tasks)
- Playbooks (step-by-step procedures)

**Store in Genome with:**
- Trigger conditions (when to suggest)
- Success rate
- Dependencies
- Version history

---

### System 9: Goal Persistence System

Never forget active goals across sessions.

**Track:**
- Current objective
- Subtasks with status
- Progress (% complete, completed items)
- Blockers with resolution status
- Session history per goal

**Behavior:**
- Auto-resume on session start
- Progress summary on resume
- Blockers surfaced immediately

---

### System 10: Automatic Documentation Engine

After every task, update:

| Document | When |
|----------|------|
| `project.md` | Project-level changes |
| `tasks.md` | Task completion or status change |
| `decision_log.md` | Architectural decisions |
| `architecture.md` | Structural changes |

**Rules:**
- Append, never overwrite (preserve history)
- Timestamp every entry
- Link decisions to code (file + line)
- Auto-generate from observation, not hallucination

---

### System 11: Memory Importance Ranking

Not all memories are equal. Rank on storage:

| Tier | Retention | Examples |
|------|-----------|---------|
| Critical | Forever | API keys, project goals, architecture decisions |
| Important | Long-term | User preferences, workflow patterns |
| Useful | Medium-term | Session results, tool outputs |
| Temporary | Short-term | Conversation context, intermediate results |

**Compression:**
- Critical → never compressed
- Important → summarized after N sessions
- Useful → summarized after N/2 sessions
- Temporary → discarded after session end

---

### System 12: Reflection Engine

After major work items (session end, milestone complete, failure):

**Analyze:**
1. What succeeded?
2. What failed?
3. What should improve?

**Create reflection with:**
- Structured format (what / why / improvement)
- Links to relevant code or conversation
- Action items for next session
- Storage in Lifeline `REFLECTIONS/`

---

### System 13: Failure Learning Engine

Every failure becomes knowledge.

**Store:**
| Field | Description |
|-------|-------------|
| Problem | What went wrong |
| Cause | Root cause analysis |
| Solution | How it was fixed |
| Lesson | Prevention strategy |

**Behavior:**
- Before retrying, check if similar failure exists in knowledge base
- Surface prevention tip for repeated failures
- Track failure patterns across sessions

---

### System 14: Cost Intelligence 2.0

**Optimize across:**
- Token usage (prompt caching, compression, context budgeting)
- Provider cost (model tiering, fallback chains)
- Latency (parallel vs sequential, streaming)
- Quality (task-to-model fit)

**Strategy:**
1. Classify task complexity
2. Route to cheapest capable model
3. Monitor success rate
4. Escalate on failure

**Display in TUI:**
- Real-time cost per session
- Token breakdown (input/output/cache/reasoning)
- Provider comparison
- Cost trends

---

### System 15: Multi-Provider Swarm

One model is not enough.

**Example routing:**
| Provider | Strengths |
|----------|-----------|
| Gemini | Coding, structured output |
| Claude | Architecture, analysis, safety |
| DeepSeek | Reasoning, math, logic |
| OpenAI | Planning, creative, instruction-following |

**Combine:**
- Task decomposition → split across providers
- Results merged by orchestrator
- Conflicts resolved by confidence scoring

---

### System 16: Environment Intelligence

Before acting, automatically understand:

- OS (Windows/Linux/macOS, version, distribution)
- GPU (model, VRAM, driver version, CUDA capability)
- CPU (architecture, cores, features)
- RAM (total, available)
- Installed tools (git, python, node, docker, etc.)
- Python version and available interpreters
- Virtual environments (venv, conda, poetry)
- Containers (docker, podman, WSL)

**Use for:**
- Tool selection (OS-native commands, fallbacks)
- Model selection (GPU availability → local models)
- Installation (package manager detection)
- Error diagnosis (environment-specific issues)

---

### System 17: Repository Intelligence

For every repository, build and maintain:

| Graph | Content |
|-------|---------|
| Dependency graph | Package dependencies (direct + transitive) |
| Architecture graph | Module structure, layers, boundaries |
| File graph | Import relationships, file dependencies |
| Knowledge graph | Domain entities, business rules, conventions |

**Generated:**
- On first encounter (full scan)
- Incrementally on changes (delta scan)
- Queriable via natural language

---

### System 18: Autonomous Testing System

After every modification:

1. Run existing tests (with timeout)
2. Generate tests for new functionality
3. Check coverage (target: 80%+)
4. Run lint (PEP8, ESLint, etc.)
5. Run type checks (mypy, TypeScript, etc.)
6. Report summary with pass/fail/coverage

**Blocking:**
- Test failures block commit (unless explicitly overridden)
- Coverage drop > 10% triggers warning and test generation

---

### System 19: Skill Marketplace

Skills become installable, shareable packages.

**Lifecycle:**
| Action | Description |
|--------|-------------|
| Install | `gogeta skill install <source>` |
| Update | `gogeta skill update <name>` |
| Share | `gogeta skill publish <name>` |
| Version | Semantic versioning, changelog |
| Rate | User ratings, usage count |
| Discover | Search by capability, category, rating |

**Format:**
- Standard SKILL.md with metadata
- Packaged as directory with assets
- Versioned and signed

---

### System 20: Project Genome

Learn project-specific patterns over time.

**Track:**
- Coding patterns (naming conventions, module structure, error handling style)
- Preferred architectures (framework choices, library preferences)
- Common workflows (build, test, deploy, debug)
- Successful fixes (bug patterns and their resolutions)

**Unique per project:**
- Stored in `~/.gogeta/genome/<project-hash>/`
- Evolves with each session
- Shared across team members (optional)

---

### System 21: Mission Control

Long-term objectives tracked across weeks or months.

**Example:**
```
Objective: Build Gogeta 3.0
```

**Track:**
- Progress (% complete, estimated vs actual)
- Milestones (completed, current, upcoming)
- Dependencies (between milestones)
- Risks (identified, mitigated, realized)
- Sessions worked per milestone

**Behavior:**
- Auto-update on task completion
- Resurface on session start
- Adjust estimates based on velocity

---

### System 22: Reality Verification System

Before claiming completion, verify:

1. File exists (if file was supposed to be created)
2. Tests pass (relevant test suite)
3. API responds (if API was modified or consumed)
4. Connector works (if connector was configured)
5. Output matches specification

**No "works on my machine" — verify in current environment.**

---

## Critical Rule: NO FAKE DATA IN THE TUI

The TUI must display REAL system state.

**Do NOT:**
- Invent values
- Generate placeholder statistics
- Show simulated metrics
- Hardcode numbers to make the interface look impressive

**Everything visible must come from an actual source.**

### Examples

| BAD | GOOD |
|-----|------|
| `Cost: $0.04` (not tracked) | `Cost: N/A` |
| `Tokens: 31k` (not tracked) | `Tokens: Not Initialized` |
| `Genome: Learning` (fake) | `Genome: 17 workflows learned` |
| `Lifeline: Active` (simulated) | `Lifeline: 3 reflections stored` |

### Required Data Source Map

| Field | Source | Function |
|-------|--------|----------|
| Model | runtime state | `gateway.current_model` |
| Session | session manager | `current_session()` |
| Cost | cost intelligence | `get_session_cost()` |
| Tokens | provider/session stats | `get_token_usage()` |
| Genome | genome storage | `workflow_count()` |
| Lifeline | lifeline directory | `reflection_count()` |
| Project | project docs | `project.md`, `tasks.md` |

### Real-Time Updates

Subscribe to Event Bus. React to events, don't poll.

| Event | UI Action |
|-------|-----------|
| `TOOL_STARTED` | Activity indicator |
| `TOOL_FINISHED` | Update stats |
| `TOOL_FAILED` | Error display |
| `SESSION_STARTED` | New session info |
| `SESSION_ENDED` | Session summary |
| `PROJECT_UPDATED` | Refresh project panel |
| `PROVIDER_COMPLETED` | Update cost/tokens |
| `MEMORY_STORED` | Memory count update |
| `REFLECTION_CREATED` | Lifeline update |

### Missing Data Policy

| Condition | Display |
|-----------|---------|
| System not initialized | `Not Initialized` |
| No data available | `No Data` |
| Feature disabled | `Disabled` |
| Error reading source | `N/A` |

### Development Rule

```
DEBUG_FAKE_DATA = True   # Only during development
DEBUG_FAKE_DATA = False  # Production — all fake metrics must disappear
```

### Verification Checklist

Before declaring any TUI field complete:

```
Field
→ Source File
→ Source Function
→ Live Updated? (YES/NO)
```

If a field cannot be traced to a real source: **REMOVE IT.**

**The Gogeta TUI is a window into the actual system — not a mockup.**
