import logging

from agent.browser_provider import BrowserProvider as CloudBrowserProvider
from agent.browser_registry import get_provider as _registry_get_browser_provider
from plugins.browser.browserbase.provider import BrowserbaseBrowserProvider as BrowserbaseProvider
from plugins.browser.browser_use.provider import BrowserUseBrowserProvider as BrowserUseProvider
from plugins.browser.firecrawl.provider import FirecrawlBrowserProvider as FirecrawlProvider
from tools.tool_backend_helpers import normalize_browser_cloud_provider

from tools.browser._state import (
    _cached_cloud_provider,
    _cloud_provider_resolved,
    logger,
)
from tools.browser._config import _get_cdp_override

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type] = {
    "browserbase": BrowserbaseProvider,
    "browser-use": BrowserUseProvider,
    "firecrawl": FirecrawlProvider,
}
_DEFAULT_PROVIDER_REGISTRY: dict[str, type] = dict(_PROVIDER_REGISTRY)


def _is_legacy_provider_registry_overridden() -> bool:
    try:
        for key, default_cls in _DEFAULT_PROVIDER_REGISTRY.items():
            if _PROVIDER_REGISTRY.get(key) is not default_cls:
                return True
        return len(_PROVIDER_REGISTRY) != len(_DEFAULT_PROVIDER_REGISTRY)
    except Exception:
        return False


def _ensure_browser_plugins_loaded() -> None:
    try:
        from gogeta_cli.plugins import _ensure_plugins_discovered
        _ensure_plugins_discovered()
    except Exception as exc:
        logger.debug("Browser plugin discovery failed (non-fatal): %s", exc)


def _get_cloud_provider() -> CloudBrowserProvider | None:
    global _cached_cloud_provider, _cloud_provider_resolved
    if _cloud_provider_resolved:
        return _cached_cloud_provider
    resolved: CloudBrowserProvider | None = None
    try:
        from gogeta_cli.config import read_raw_config
        cfg = read_raw_config()
        browser_cfg = cfg.get("browser", {})
        provider_key = None
        if isinstance(browser_cfg, dict) and "cloud_provider" in browser_cfg:
            provider_key = normalize_browser_cloud_provider(browser_cfg.get("cloud_provider"))
            if provider_key == "local":
                _cached_cloud_provider = None
                _cloud_provider_resolved = True
                return None
        if provider_key:
            try:
                if _is_legacy_provider_registry_overridden():
                    factory = _PROVIDER_REGISTRY.get(provider_key)
                    if factory is not None:
                        resolved = factory()
                else:
                    _ensure_browser_plugins_loaded()
                    resolved = _registry_get_browser_provider(provider_key)
                    if resolved is None:
                        logger.warning(
                            "browser.cloud_provider=%r is not a registered browser plugin; "
                            "falling back to auto-detect (install the corresponding plugin "
                            "or fix the config key spelling).",
                            provider_key,
                        )
            except Exception:
                logger.warning(
                    "Failed to instantiate explicit cloud_provider %r; will retry on next call",
                    provider_key,
                    exc_info=True,
                )
                return None
    except Exception as e:
        logger.debug("Could not read cloud_provider from config: %s", e)
    if resolved is None:
        try:
            fallback_provider = BrowserUseProvider()
            if fallback_provider.is_configured():
                resolved = fallback_provider
            else:
                fallback_provider = BrowserbaseProvider()
                if fallback_provider.is_configured():
                    resolved = fallback_provider
        except Exception:
            logger.debug("Cloud provider auto-detect failed", exc_info=True)
            return None
    if resolved is None:
        return None
    _cached_cloud_provider = resolved
    _cloud_provider_resolved = True
    return _cached_cloud_provider


def _is_local_mode() -> bool:
    if _get_cdp_override():
        return False
    return _get_cloud_provider() is None


def _is_local_backend() -> bool:
    try:
        from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
        return _is_camofox_mode() or _get_cloud_provider() is None
    except ImportError:
        return _get_cloud_provider() is None


def _ensure_cdp_supervisor(task_id: str) -> None:
    from tools.browser._config import _get_cdp_override, _resolve_cdp_override, _get_dialog_policy_config
    cdp_url = _get_cdp_override()
    if not cdp_url:
        from tools.browser._state import _active_sessions, _cleanup_lock
        with _cleanup_lock:
            session_info = _active_sessions.get(task_id, {})
        maybe = str(session_info.get("cdp_url") or "")
        if maybe:
            cdp_url = _resolve_cdp_override(maybe)
    if not cdp_url:
        return
    try:
        from tools.browser_supervisor import SUPERVISOR_REGISTRY
        policy, timeout_s = _get_dialog_policy_config()
        SUPERVISOR_REGISTRY.get_or_start(
            task_id=task_id,
            cdp_url=cdp_url,
            dialog_policy=policy,
            dialog_timeout_s=timeout_s,
        )
    except Exception as exc:
        logger.debug(
            "CDP supervisor attach for task=%s failed (non-fatal): %s",
            task_id, exc,
        )


def _stop_cdp_supervisor(task_id: str) -> None:
    try:
        from tools.browser_supervisor import SUPERVISOR_REGISTRY
        SUPERVISOR_REGISTRY.stop(task_id)
    except Exception as exc:
        logger.debug("CDP supervisor stop for task=%s failed (non-fatal): %s", task_id, exc)
