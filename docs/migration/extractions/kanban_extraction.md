# Kanban Watcher Extraction

## Summary

Extracted the kanban watcher subsystem from `gateway/run.py` into `gateway/watchers/kanban.py` using the mixin pattern established by `TelegramTopicMixin`.

### Lines Removed from run.py

- **1,036 lines** removed (from 18,384 down to 17,348 — -5.6%)
- Total run.py reduction since Phase 1 began: ~1,768 lines (19,116 → 17,348)

### New Files Created

| File | Size | Purpose |
|------|------|---------|
| `gateway/watchers/__init__.py` | 0 lines | Package marker |
| `gateway/watchers/kanban.py` | ~750 lines | `KanbanWatcherMixin` with 6 methods |

### Methods Extracted

| Method | Type | Complexity |
|--------|------|------------|
| `_kanban_notifier_watcher` | async | Polls kanban DB for terminal events; delivers notifications via adapters |
| `_kanban_dispatcher_watcher` | async | Embedded kanban dispatcher loop; spawns workers for ready tasks |
| `_deliver_kanban_artifacts` | async | Uploads artifact files (images, docs, video) referenced by completed tasks |
| `_kanban_advance` | sync (to_thread) | Advances notification cursor in kanban DB |
| `_kanban_unsub` | sync (to_thread) | Removes notification subscription |
| `_kanban_rewind` | sync (to_thread) | Rewinds claimed cursor after send failure |

### Dependencies

#### Added (in `watchers/kanban.py`)

- `asyncio`, `logging`, `os`, `sqlite3`, `time`, `pathlib`, `typing`
- `gateway.platforms.base.BasePlatformAdapter` (for `filter_local_delivery_paths`)

#### Inline imports preserved (same as original)

- `gogeta_cli.kanban_db` — DB operations
- `gogeta_cli.config` — config loading
- `gogeta_cli.kanban_decompose` — auto-decomposition
- `gateway.config.Platform` — platform enum
- `urllib.parse.quote` — URL encoding for file URIs

### Runtime Contract

`KanbanWatcherMixin` expects `self` to provide:

| Attribute | Type | Origin |
|-----------|------|--------|
| `self._running` | `bool` | GatewayRunner shutdown flag |
| `self.adapters` | `dict[Platform, Adapter]` | Connected platform adapters |
| `self._active_profile_name()` | method -> `str` | Returns current profile name |
| `self._kanban_sub_fail_counts` | `dict[tuple, int]` | Per-subscription send failure counter (lazy) |
| `self._kanban_notifier_profile` | `str` | Cached profile name for notifier filtering (lazy) |

### Change Log

- `gateway/run.py` line 18: added `from gateway.watchers.kanban import KanbanWatcherMixin`
- `gateway/run.py` line 905: updated to `class GatewayRunner(TelegramTopicMixin, KanbanWatcherMixin):`
- `gateway/run.py` lines 4096–5131: deleted (6 kanban watcher methods)
- Line 1025 `self._kanban_notifier_profile = self._active_profile_name()` preserved in `__init__`
- Lines 3676–3685 launcher code (`asyncio.create_task` calls) preserved — unchanged

### Test Results

| Suite | Tests | Result |
|-------|-------|--------|
| PII redaction | 16 | Passed |
| SSL certs + loop + replay | 35 | Passed |
| Notifications | 48 | Passed |
| Telegram topic mode + DM topics | 80 | Passed |

### Architecture Enforcer

- Files scanned: **594** (was 592; +2 from new watchers)
- Violations: **626** (unchanged from baseline)
- No net new violations introduced.

### Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Broken `_handle_kanban_command` refs | Low | Only ref is `self._kanban_notifier_profile` (lazy attr) — unchanged |
| Log filter breakage | Low | Watchers log under `gateway.watchers.kanban` instead of `gateway.run` |
| Import cycle | None | `kanban.py` imports only stable gateway/CLI modules; no circular deps |
| Test patch targets | None | Tests patch `gateway.run` module-level names, not instance methods |

### Remaining Watcher Candidates

| Candidate | Lines | File Target | Priority |
|-----------|-------|-------------|----------|
| `_handoff_watcher` + `_session_expiry_watcher` | ~380 | `gateway/watchers/session.py` | Medium |
| `_platform_reconnect_watcher` | ~TBD | `gateway/watchers/platform.py` | Medium |
| `_run_process_watcher` | ~TBD | `gateway/watchers/process.py` | Low |
| `_run_planned_stop_watcher` | ~TBD | `gateway/watchers/process.py` | Low |
