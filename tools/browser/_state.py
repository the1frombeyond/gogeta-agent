import atexit
import logging
import os
import threading

logger = logging.getLogger(__name__)

_SANE_PATH_DIRS = (
    "/data/data/com.termux/files/usr/bin",
    "/data/data/com.termux/files/usr/sbin",
    "/opt/homebrew/bin",
    "/opt/homebrew/sbin",
    "/usr/local/sbin",
    "/usr/local/bin",
    "/usr/sbin",
    "/usr/bin",
    "/sbin",
    "/bin",
)
_SANE_PATH = os.pathsep.join(_SANE_PATH_DIRS)

_last_screenshot_cleanup_by_dir: dict[str, float] = {}

DEFAULT_COMMAND_TIMEOUT = 30
SNAPSHOT_SUMMARIZE_THRESHOLD = 8000
_EMPTY_OK_COMMANDS: frozenset = frozenset({"close", "record"})

_cached_command_timeout: int | None = None
_command_timeout_resolved = False

_cached_cloud_provider = None
_cloud_provider_resolved = False
_allow_private_urls_resolved = False
_cached_allow_private_urls: bool | None = None
_cached_agent_browser: str | None = None
_agent_browser_resolved = False

_cached_browser_engine: str | None = None
_browser_engine_resolved = False

_auto_local_for_private_urls_resolved = False
_cached_auto_local_for_private_urls: bool = True

_active_sessions: dict[str, dict[str, str]] = {}
_recording_sessions: set = set()

_last_active_session_key: dict[str, str] = {}
_LOCAL_SUFFIX = "::local"

_cleanup_done = False

BROWSER_SESSION_INACTIVITY_TIMEOUT = int(os.environ.get("BROWSER_INACTIVITY_TIMEOUT", "300"))

_session_last_activity: dict[str, float] = {}

_cleanup_thread = None
_cleanup_running = False
_cleanup_lock = threading.Lock()
