#!/usr/bin/env python3
"""
Backward-compatibility shim for ``tools.browser_tool``.

All code has moved to ``tools/browser/`` package. This module re-exports
everything from ``tools.browser`` so that existing imports like::

    from tools.browser_tool import browser_navigate, cleanup_all_browsers

continue to work without modification.

New code should import directly from ``tools.browser`` instead.
"""

# ruff: noqa: F401, F403 — intentional re-export

from tools.browser import *

# Re-export underscore-prefixed names not captured by wildcard import
# (public tool functions)
from tools.browser.cleanup import (
    cleanup_browser,
    cleanup_all_browsers,
    _emergency_cleanup_all_sessions,
)
from tools.browser._session import (
    _last_session_key,
    _is_local_sidecar_key,
    _get_session_info,
)
from tools.browser._config import (
    _get_cdp_override,
    _resolve_cdp_override,
    _get_command_timeout,
    _get_vision_model,
    _get_extraction_model,
    _get_dialog_policy_config,
    _merge_browser_path,
    _socket_safe_tmpdir,
    _discover_homebrew_node_dirs,
    _browser_candidate_path_dirs,
)
from tools.browser._cloud import (
    _get_cloud_provider,
    _is_local_mode,
    _is_local_backend,
    _ensure_cdp_supervisor,
    _stop_cdp_supervisor,
    _is_legacy_provider_registry_overridden,
    _ensure_browser_plugins_loaded,
    _PROVIDER_REGISTRY,
    _DEFAULT_PROVIDER_REGISTRY,
)
from tools.browser._engine import (
    _get_browser_engine,
    _should_inject_engine,
    _using_lightpanda_engine,
    _lightpanda_fallback_reason,
    _needs_lightpanda_fallback,
    _annotate_lightpanda_fallback,
    _copy_fallback_warning,
)
from tools.browser._exec import (
    _run_browser_command,
    _run_chrome_fallback_command,
    _chrome_fallback_screenshot,
    _find_agent_browser,
    _extract_screenshot_path_from_text,
    _browser_install_hint,
    _maybe_start_recording,
    _maybe_stop_recording,
)
from tools.browser._content import (
    _extract_relevant_content,
    _truncate_snapshot,
)
from tools.browser._private import (
    _url_is_private,
    _allow_private_urls,
    _auto_local_for_private_urls,
)
from tools.browser._requirements import (
    check_browser_requirements,
    check_browser_vision_requirements,
    _chromium_installed,
    _chromium_search_roots,
    _running_in_docker,
)
from tools.browser._state import (
    _active_sessions,
    _recording_sessions,
    _cleanup_lock,
    _cleanup_done,
    _last_active_session_key,
    _LOCAL_SUFFIX,
    _session_last_activity,
    _last_screenshot_cleanup_by_dir,
    BROWSER_SESSION_INACTIVITY_TIMEOUT,
    SNAPSHOT_SUMMARIZE_THRESHOLD,
    _SANE_PATH,
)

# Legacy provider aliases (already re-exported by tools.browser)
from agent.browser_provider import BrowserProvider as CloudBrowserProvider
from plugins.browser.browserbase.provider import BrowserbaseBrowserProvider as BrowserbaseProvider
from plugins.browser.browser_use.provider import BrowserUseBrowserProvider as BrowserUseProvider
from plugins.browser.firecrawl.provider import FirecrawlBrowserProvider as FirecrawlProvider
