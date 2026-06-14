# ---------------------------------------------------------------------------
# tools/browser/__init__.py
#
# Public API re-exports, BROWSER_TOOL_SCHEMAS, and registry registration.
# This module serves as the canonical entry point; a backward-compat shim at
# tools/browser_tool.py re-exports everything from here.
# ---------------------------------------------------------------------------

# Re-export public tool functions
from tools.browser.navigate import browser_navigate, _navigation_session_key
from tools.browser.snapshot import browser_snapshot
from tools.browser.interact import browser_click, browser_type, browser_scroll, browser_back, browser_press
from tools.browser.console import browser_console, _browser_eval, _camofox_eval
from tools.browser.vision import browser_get_images, browser_vision
from tools.browser.cleanup import cleanup_browser, cleanup_all_browsers, _emergency_cleanup_all_sessions
from tools.browser._session import _last_session_key, _is_local_sidecar_key, _get_session_info
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
from tools.browser._engine import _get_browser_engine
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
    CloudBrowserProvider,
    BrowserbaseProvider,
    BrowserUseProvider,
    FirecrawlProvider,
)
from tools.browser._engine import (
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
from tools.browser._content import _extract_relevant_content, _truncate_snapshot
from tools.browser._private import _url_is_private, _allow_private_urls, _auto_local_for_private_urls
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

# ---------------------------------------------------------------------------
# Tool Schemas
# ---------------------------------------------------------------------------

BROWSER_TOOL_SCHEMAS = [
    {
        "name": "browser_navigate",
        "description": "Navigate to a URL in the browser. Initializes the session and loads the page. Must be called before other browser tools. For simple information retrieval, prefer web_search or web_extract (faster, cheaper). For plain-text endpoints — URLs ending in .md, .txt, .json, .yaml, .yml, .csv, .xml, raw.githubusercontent.com, or any documented API endpoint — prefer curl via the terminal tool or web_extract; the browser stack is overkill and much slower for these. Use browser tools when you need to interact with a page (click, fill forms, dynamic content). Returns a compact page snapshot with interactive elements and ref IDs — no need to call browser_snapshot separately after navigating.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to (e.g., 'https://example.com')"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "browser_snapshot",
        "description": "Get a text snapshot of the current page using the accessibility tree. Use this after navigating to a page to see its content as structured text — links, buttons, headings, and text are preserved as an accessibility tree with ref IDs for interaction. Supports optional task-aware content extraction: when you pass the current user_task, we use AI to extract only the relevant parts of large pages (like search results or documentation). Use instead of screenshots for LLM agents — text is faster and more accurate for reading. Call after browser_navigate to see page content.",
        "parameters": {
            "type": "object",
            "properties": {
                "full": {
                    "type": "boolean",
                    "description": "If set to true, returns the full page snapshot without AI summarization. Default: False (AI-summarized based on the current user task if available)"
                },
                "user_task": {
                    "type": "string",
                    "description": "Optional: The user's task description to focus the AI extraction on relevant content only. When provided, only content relevant to this task is returned."
                }
            }
        }
    },
    {
        "name": "browser_click",
        "description": "Click an interactive element on the current page using its reference ID (like @e5). Reference IDs are obtained from the snapshot returned by browser_navigate or browser_snapshot. The snapshot lists interactive elements with labels like [ref=e5]. Use this ref value for clicking. Works for links, buttons, checkboxes, and other clickable elements.",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "The reference ID of the element to click (e.g., '@e5'). Get this from the page snapshot."
                }
            },
            "required": ["ref"]
        }
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field, text area, or other editable element. Reference IDs are obtained from the browser snapshot. The text is typed into the element identified by its ref ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "The reference ID of the input element (e.g., '@e12' or '@search-box')."
                },
                "text": {
                    "type": "string",
                    "description": "The text to type into the element."
                }
            },
            "required": ["ref", "text"]
        }
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the page in the specified direction. Useful for long pages, search results, or infinite-scroll content. Reference IDs remain valid after scrolling if elements stay in the DOM.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "description": "Scroll direction: 'down' or 'up'",
                    "default": "down"
                }
            }
        }
    },
    {
        "name": "browser_back",
        "description": "Navigate back to the previous page in the browser history. Equivalent to clicking the browser back button.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "browser_press",
        "description": "Press a keyboard key (like Enter, Escape, Tab) on the current page. Useful for submitting forms, dismissing dialogs, or navigating between fields.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to press (e.g., 'Enter', 'Escape', 'Tab', 'ArrowDown', 'ArrowUp')"
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "browser_get_images",
        "description": "Get all images from the current page as descriptions. Takes a screenshot and uses AI vision to identify and describe all images visible on the page. Returns structured image descriptions.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "browser_vision",
        "description": "Ask a visual question about the current page. Takes a screenshot and sends it to a vision-enabled model. Use this for visual tasks where you need to understand page layout, see images/photos, verify visual styling, or interpret charts and graphs. Much slower than text-based browser_snapshot — prefer text-based snapshots for reading content.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question about what you want to see or understand on the page."
                },
                "annotate": {
                    "type": "boolean",
                    "description": "If true, returns an annotated screenshot with numbered elements. Default: False."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "browser_console",
        "description": "Access the browser console — read console logs, errors, or evaluate JavaScript expressions. Use for debugging web pages, checking for JavaScript errors, or executing JavaScript in the page context. When 'clear' is true, clears all console output. When 'expression' is provided, evaluates it as JavaScript and returns the result.",
        "parameters": {
            "type": "object",
            "properties": {
                "clear": {
                    "type": "boolean",
                    "description": "If true, clears the browser console. Default: False."
                },
                "expression": {
                    "type": "string",
                    "description": "A JavaScript expression to evaluate in the browser context (e.g., 'document.title', 'window.scrollY')."
                }
            }
        }
    },
]

# ---------------------------------------------------------------------------
# Registry Registration
# ---------------------------------------------------------------------------

from tools.registry import registry, tool_error

_BROWSER_SCHEMA_MAP = {s["name"]: s for s in BROWSER_TOOL_SCHEMAS}

registry.register(
    name="browser_navigate",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_navigate"],
    handler=lambda args, **kw: browser_navigate(url=args.get("url", ""), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\U0001f310",
)

registry.register(
    name="browser_snapshot",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_snapshot"],
    handler=lambda args, **kw: browser_snapshot(
        full=args.get("full", False), task_id=kw.get("task_id"), user_task=kw.get("user_task")),
    check_fn=check_browser_requirements,
    emoji="\U0001f4f8",
)

registry.register(
    name="browser_click",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_click"],
    handler=lambda args, **kw: browser_click(ref=args.get("ref", ""), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\U0001f446",
)

registry.register(
    name="browser_type",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_type"],
    handler=lambda args, **kw: browser_type(ref=args.get("ref", ""), text=args.get("text", ""), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\u2328\ufe0f",
)

registry.register(
    name="browser_scroll",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_scroll"],
    handler=lambda args, **kw: browser_scroll(direction=args.get("direction", "down"), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\U0001f4dc",
)

registry.register(
    name="browser_back",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_back"],
    handler=lambda args, **kw: browser_back(task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\u25c0\ufe0f",
)

registry.register(
    name="browser_press",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_press"],
    handler=lambda args, **kw: browser_press(key=args.get("key", ""), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\u2328\ufe0f",
)

registry.register(
    name="browser_get_images",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_get_images"],
    handler=lambda args, **kw: browser_get_images(task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\U0001f5bc\ufe0f",
)

registry.register(
    name="browser_vision",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_vision"],
    handler=lambda args, **kw: browser_vision(question=args.get("question", ""), annotate=args.get("annotate", False), task_id=kw.get("task_id")),
    check_fn=check_browser_vision_requirements,
    emoji="\U0001f441\ufe0f",
)

registry.register(
    name="browser_console",
    toolset="browser",
    schema=_BROWSER_SCHEMA_MAP["browser_console"],
    handler=lambda args, **kw: browser_console(clear=args.get("clear", False), expression=args.get("expression"), task_id=kw.get("task_id")),
    check_fn=check_browser_requirements,
    emoji="\u25b6\ufe0f",
)

# ---------------------------------------------------------------------------
# Legacy provider aliases (backward compat)
# ---------------------------------------------------------------------------
from agent.browser_provider import BrowserProvider as CloudBrowserProvider
from plugins.browser.browserbase.provider import BrowserbaseBrowserProvider as BrowserbaseProvider
from plugins.browser.browser_use.provider import BrowserUseBrowserProvider as BrowserUseProvider
from plugins.browser.firecrawl.provider import FirecrawlBrowserProvider as FirecrawlProvider

# Cleanup thread lifecycle
from tools.browser._session import _start_browser_cleanup_thread, _stop_browser_cleanup_thread, _cleanup_inactive_browser_sessions
