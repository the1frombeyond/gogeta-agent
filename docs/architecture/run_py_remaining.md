# `run.py` Remaining Sections — Analysis

**File:** `gateway/run.py`
**Lines:** 16,483
**Watcher extraction:** Complete (Phases 2–5, −2,633 lines)

---

## Section Breakdown

### 1. Gateway Topology (lines 1–850)
Module docstring, imports, config loading utilities, `_load_gateway_config()`, `should_exit_cleanly`/`_with_failure`/`exit_reason`/`exit_code` sentinels, `_connect_adapter_with_timeout`, `_safe_adapter_disconnect`, `_handle_adapter_fatal_error`, `_handle_active_session_busy_message`, GatewayRunner class preamble and `__init__` (~118 instance attributes including adapters, config, session_store, agent_cache, etc.).

- **Lines:** ~850
- **Responsibility:** Module wiring + class construction
- **Coupling:** Tight — every downstream reference touches these imports and config values
- **Difficulty to extract:** EXTREME — `__init__` wires 100+ attributes in one block; splitting requires constructor decomposition or a builder pattern

---

### 2. Voice Engine (lines ~9200–9700)
`_handle_voice_command`, `_handle_voice_channel_join`, `_handle_voice_channel_leave`, `_handle_voice_channel_input`, `_send_voice_reply`.

- **Lines:** ~500
- **Responsibility:** Real-time voice channel lifecycle, transcription dispatch, voice reply sending
- **Coupling:** MEDIUM — voice methods reference `self.adapters`, `self._handle_message`, `self.config`, `self._running`, but are mostly self-contained with their own state
- **Difficulty to extract:** MEDIUM — the voice channel join/leave/input loop has complex asyncio concurrency but few outside dependencies

---

### 3. Slash Commands (lines ~7300–11900)
40+ `_handle_*_command` methods: `_handle_reset_command`, `_handle_profile_command`, `_handle_whoami_command`, `_handle_kanban_command`, `_handle_status_command`, `_handle_agents_command`, `_handle_stop_command`, `_handle_platform_command`, `_handle_restart_command`, `_handle_version_command`, `_handle_help_command`, `_handle_commands_command`, `_handle_model_command`, `_handle_codex_runtime_command`, `_handle_personality_command`, `_handle_retry_command`, `_handle_goal_command`, `_handle_subgoal_command`, `_handle_undo_command`, `_handle_set_home_command`, `_handle_voice_command`, `_handle_rollback_command`, `_handle_background_command`, `_handle_reasoning_command`, `_handle_fast_command`, `_handle_yolo_command`, `_handle_verbose_command`, `_handle_footer_command`, `_handle_compress_command`, `_handle_title_command`, `_handle_resume_command`, `_handle_branch_command`, `_handle_usage_command`, `_handle_insights_command`, `_handle_reload_mcp_command`, `_handle_reload_skills_command`, `_handle_bundles_command`, `_handle_approve_command`, `_handle_deny_command`, `_handle_debug_command`, `_handle_update_command`, `_on_confirm` (MCP reload), `_request_slash_confirm`.

- **Lines:** ~4,600
- **Responsibility:** Dispatch 40+ gateway slash commands, each with its own validation, state mutation, and response formatting
- **Coupling:** MEDIUM — each handler is fairly self-contained (read `self.*`, produce side effects, send response). Shared infrastructure: `_request_slash_confirm`, `_on_confirm` (approval gating), `_handle_message` for dispatch of synthetic responses.
- **Difficulty to extract:** HIGH — 40 methods is a lot of surface; natural groupings exist (session commands, config commands, model commands, MCP commands) but the dispatch routing table and confirmation infrastructure are intertwined.

---

### 4. Message Processing (lines ~4600–7300)
`_handle_message`, `_handle_message_with_agent`, `_prepare_inbound_message_text`, `_enrich_message_with_vision`, `_enrich_message_with_transcription`, `_inject_watch_notification`, `_interrupt_and_clear_session`, `_handle_reset_command`.

- **Lines:** ~2,700
- **Responsibility:** Core inbound message pipeline — parse, enrich (vision/transcription), dispatch to agent, handle responses
- **Coupling:** HIGH — `_handle_message` is the central hub that everything routes through; references config, adapters, session_store, agent_cache, _running_agents, progress system
- **Difficulty to extract:** EXTREME — the message processing chain has the most entangled dependency tree in the file

---

### 5. Agent Execution (lines ~13000–15300)
`_run_agent`, `_run_agent_via_proxy`, `track_agent`, `monitor_for_interrupt`, `_start_stream_consumer`, `_notify_long_running`, progress callbacks, `run_sync`, `voice_ack_callback`.

- **Lines:** ~2,300
- **Responsibility:** Agent invocation, streaming, interrupt monitoring, progress reporting
- **Coupling:** HIGH — `_run_agent` is the core execution path; references config, model overrides, provider selection, interrupt machinery, voice ack, progress messaging
- **Difficulty to extract:** EXTREME — deeply interleaved with message processing and voice; the progress callback chain alone spans 3 methods that cross-cut with slash commands

---

### 6. Drain & Restart (lines ~2400–3700)
`_drain_active_agents`, `_notify_active_sessions_of_shutdown`, `_launch_detached_restart_command`, `request_restart`, `_run_restart`, `start`, `stop`, `_stop_impl`, `wait_for_shutdown`.

- **Lines:** ~1,300
- **Responsibility:** Graceful shutdown, drain active sessions, restart orchestration
- **Coupling:** MEDIUM — references `self.adapters`, `self._running_agents`, `self._exit_code`; the restart command builder is fairly isolated
- **Difficulty to extract:** MEDIUM — `start()` and `stop()` are the gateway entry/exit points; extraction risks breaking the lifecycle sequence

---

### 7. Goal/Background (lines ~8800–9200, ~9800–10100)
`_handle_goal_command`, `_handle_subgoal_command`, `_send_goal_status_notice`, `_defer_goal_status_notice_after_delivery`, `_deliver`, `_post_turn_goal_continuation`, `_handle_background_command`, `_run_background_task`, `run_sync`.

- **Lines:** ~1,100
- **Responsibility:** Goal-driven continuation loop, background process launch and management
- **Coupling:** MEDIUM — goal system references `_handle_message`, `_run_agent`, progress system; background system is relatively isolated
- **Difficulty to extract:** HIGH — goal continuation is a recursive loop that calls back into message processing; requires careful interface design

---

### 8. Progress Messages (lines ~13700–14300)
`send_progress_messages`, `_edit_progress_message`, `_send_progress_text`, `_roll_progress_overflow_if_needed`.

- **Lines:** ~600
- **Responsibility:** Edit/update progress messages during long-running agent turns
- **Coupling:** LOW — mostly reads config and calls `adapter.edit()`; standalone enough
- **Difficulty to extract:** LOW — could be extracted as a mixin immediately

---

### 9. Gateway Startup (lines ~15500–16483)
`start_gateway`, `shutdown_signal_handler`, `restart_signal_handler`, `_start_cron_ticker`, `main` (CLI entry).

- **Lines:** ~980
- **Responsibility:** Bootstrap the gateway, register signal handlers, manage PID file, start cron, parse CLI args
- **Coupling:** LOW — standalone functions that construct and call `GatewayRunner`
- **Difficulty to extract:** LOW — `start_gateway` is a ~400-line module-level function that could be moved to `gateway/runner.py` or `gateway/bootstrap.py`

---

## Summary

| Section | Lines | Extraction Difficulty |
|---|---|---|
| Gateway Topology (imports, config, `__init__`) | ~850 | EXTREME |
| Voice Engine | ~500 | MEDIUM |
| Slash Commands | ~4,600 | HIGH |
| Message Processing | ~2,700 | EXTREME |
| Agent Execution | ~2,300 | EXTREME |
| Drain & Restart | ~1,300 | MEDIUM |
| Goal/Background | ~1,100 | HIGH |
| Progress Messages | ~600 | LOW |
| Gateway Startup | ~980 | LOW |

**Priority ranking for further decomposition (highest leverage first):**

1. **Gateway Startup** — move `start_gateway` + signal handlers + `main` to `gateway/bootstrap.py` (quick win, −980 lines)
2. **Progress Messages** — extract as `ProgressMixin` (quick win, −600 lines)
3. **Voice Engine** — extract as `VoiceMixin` (moderate complexity, −500 lines)
4. **Drain & Restart** — extract as `LifecycleMixin` (moderate complexity, −1,300 lines)
5. **Slash Commands** — needs architectural design for command registration pattern before extraction

**Do not attempt without new architecture:**
- Message Processing + Agent Execution — these should be unified into a proper pipeline with the Tool Registry and Event Bus, not extracted into another mixin
