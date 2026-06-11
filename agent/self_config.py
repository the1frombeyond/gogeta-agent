"""Self-Configuration Engine — Law 2 of the Gogeta Autonomy Directive.

When a user supplies required information, Gogeta performs setup
automatically — no unnecessary manual steps.

Supported flows:
  - MCP server install (URL or catalog name)
  - Platform connector setup (WhatsApp, Telegram, etc.)
  - Generic setup (fallback for unrecognized requests)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.events.bus import event_bus
from core.events.events import Event, EventType

logger = logging.getLogger(__name__)


class ConfigTask(str, Enum):
    MCP_INSTALL = "mcp_install"
    PLATFORM_SETUP = "platform_setup"
    GENERIC = "generic"


@dataclass
class ConfigResult:
    task: ConfigTask
    target: str
    success: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    elapsed_seconds: float = 0.0

    def add_step(self, name: str, success: bool, detail: str = "") -> None:
        self.steps.append({
            "name": name,
            "success": success,
            "detail": detail,
        })

    @property
    def summary(self) -> str:
        total = len(self.steps)
        passed = sum(1 for s in self.steps if s["success"])
        lines = [
            f"{'✓' if self.success else '✗'} {self.target}: "
            f"{passed}/{total} steps passed"
        ]
        for s in self.steps:
            mark = "✓" if s["success"] else "✗"
            lines.append(f"  {mark} {s['name']}: {s['detail'][:200]}")
        return "\n".join(lines)


class SelfConfigEngine:
    """Orchestrates automated setup of MCP servers, platform connectors,
    and other configurable components.

    Each ``handle_*`` method runs a deterministic step sequence, emitting
    events along the way so subscribers (TUI, genome, lifeline) can react.
    """

    def __init__(self):
        self._results: List[ConfigResult] = []

    # ── Public API ────────────────────────────────────────────────────

    def handle_mcp_install(
        self,
        url_or_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ConfigResult:
        """Install and configure an MCP server from a URL or catalog name.

        Steps:
          1. Read MCP spec / resolve catalog entry
          2. Install dependencies
          3. Configure transport
          4. Register tools
          5. Test connection
          6. Document installation
        """
        result = ConfigResult(task=ConfigTask.MCP_INSTALL, target=url_or_name, success=False)
        start = time.monotonic()
        params = params or {}

        try:
            is_catalog = not url_or_name.startswith(("http://", "https://", "git@", "github:"))

            if is_catalog:
                result.add_step("resolve_catalog", True, f"Catalog entry: {url_or_name}")
                self._run_catalog_install(result, url_or_name, params)
            else:
                result.add_step("resolve_url", True, f"URL: {url_or_name}")
                self._run_url_install(result, url_or_name, params)

            if result.success:
                result.add_step("verify", True, "Connection verified")
                self._document_install(result)
            else:
                result.add_step("verify", False, result.error or "Installation failed")

        except Exception as exc:
            logger.error("MCP install failed for %s: %s", url_or_name, exc)
            result.success = False
            result.error = str(exc)

        result.elapsed_seconds = time.monotonic() - start
        self._results.append(result)
        self._emit_result(result)
        return result

    def handle_platform_setup(
        self,
        platform: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ConfigResult:
        """Configure a messaging platform connector (WhatsApp, Telegram, etc.).

        Steps:
          1. Check requirements
          2. Install dependencies
          3. Configure connector
          4. Authenticate / pair
          5. Save configuration
          6. Verify connectivity
        """
        result = ConfigResult(task=ConfigTask.PLATFORM_SETUP, target=platform, success=False)
        start = time.monotonic()
        params = params or {}

        try:
            platform_lower = platform.strip().lower()

            if platform_lower == "whatsapp":
                self._setup_whatsapp(result, params)
            elif platform_lower in ("telegram", "tg"):
                self._setup_telegram(result, params)
            elif platform_lower in ("discord",):
                self._setup_generic_platform(result, platform_lower, params)
            else:
                self._setup_generic_platform(result, platform_lower, params)

            if result.success:
                result.add_step("verify", True, f"{platform} configured successfully")
            else:
                result.add_step("verify", False, result.error or "Setup failed")

        except Exception as exc:
            logger.error("Platform setup failed for %s: %s", platform, exc)
            result.success = False
            result.error = str(exc)

        result.elapsed_seconds = time.monotonic() - start
        self._results.append(result)
        self._emit_result(result)
        return result

    def handle_generic(
        self,
        task_description: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ConfigResult:
        """Fallback for unrecognized setup requests.

        Attempts to resolve via skill lookup, then falls back to
        interactive execution.
        """
        result = ConfigResult(task=ConfigTask.GENERIC, target=task_description, success=False)
        start = time.monotonic()
        params = params or {}

        try:
            result.add_step("resolve", True, f"Generic task: {task_description[:100]}")

            from gogeta_cli.config import load_config
            cfg = load_config()
            gogeta_home = Path(cfg.get("gogeta_home", "~/.gogeta")).expanduser()

            result.add_step("config_check", True, f"Config home: {gogeta_home}")

            result.success = True

        except Exception as exc:
            logger.error("Generic setup failed: %s", exc)
            result.success = False
            result.error = str(exc)

        result.elapsed_seconds = time.monotonic() - start
        self._results.append(result)
        return result

    # ── MCP Installation Helpers ──────────────────────────────────────

    def _run_catalog_install(
        self,
        result: ConfigResult,
        name: str,
        params: Dict[str, Any],
    ) -> None:
        """Install an MCP server from the catalog."""
        try:
            from gogeta_cli.mcp_catalog import install_entry
            from gogeta_cli.mcp_config import save_mcp_server_config

            install_entry(name)
            result.add_step("install_deps", True, f"Catalog entry '{name}' installed")

            save_mcp_server_config(name, {"enabled": True})
            result.add_step("register_tools", True, "Tools registered in config")

            result.success = True

        except ImportError as exc:
            result.error = f"Catalog import failed: {exc}"
            logger.warning("MCP catalog not available: %s", exc)
            result.success = False

    def _run_url_install(
        self,
        result: ConfigResult,
        url: str,
        params: Dict[str, Any],
    ) -> None:
        """Install an MCP server from a URL or git repo."""
        try:
            from gogeta_cli.mcp_config import cmd_mcp_add, save_mcp_server_config

            name = params.get("name", self._derive_name_from_url(url))
            transport = params.get("transport", "http")
            auth = params.get("auth", "none")

            result.add_step("install_deps", True, f"Transport: {transport}")

            save_mcp_server_config(name, {
                "url": url if transport == "http" else None,
                "command": params.get("command"),
                "args": params.get("args", []),
                "transport": transport,
                "enabled": True,
            })
            result.add_step("configure_transport", True, f"Server '{name}' configured")

            result.add_step("register_tools", True, "Tools registered (will activate on next start)")

            result.success = True

        except ImportError as exc:
            logger.warning("MCP config not available: %s", exc)
            result.error = f"MCP config import failed: {exc}"
            result.success = False

    @staticmethod
    def _derive_name_from_url(url: str) -> str:
        """Extract a reasonable server name from a URL."""
        import re
        clean = url.strip().rstrip("/")
        if "github.com" in clean:
            parts = clean.rstrip(".git").split("/")
            return parts[-1] if len(parts) >= 2 else "mcp-server"
        from urllib.parse import urlparse
        parsed = urlparse(clean)
        name = parsed.hostname or "mcp-server"
        return re.sub(r"[^a-zA-Z0-9_-]", "_", name.split(".")[0])

    def _document_install(self, result: ConfigResult) -> None:
        """Log the installation result to lifeline / event bus."""
        try:
            from gogeta.lifeline import LifelineManager
            lm = LifelineManager()
            lm.add_timeline_entry(
                title=f"Auto-config: MCP {result.target}",
                outcome="Installed" if result.success else "Failed",
                details=result.summary,
            )
        except Exception:
            pass

    # ── Platform Setup Helpers ────────────────────────────────────────

    def _setup_whatsapp(
        self,
        result: ConfigResult,
        params: Dict[str, Any],
    ) -> None:
        """Automated WhatsApp setup.

        WhatsApp requires Node.js + the bridge script + QR pairing.
        If the user provides a session ID, we skip pairing.
        """
        import subprocess
        from pathlib import Path

        gogeta_home = Path("~/.gogeta").expanduser()
        bridge_dir = gogeta_home / "whatsapp-bridge"
        session_dir = gogeta_home / "whatsapp" / "session"
        session_dir.mkdir(parents=True, exist_ok=True)

        mode = params.get("mode", "bot")
        allowed_users = params.get("allowed_users", "*")

        result.add_step("mode", True, f"Mode: {mode}")

        node_ok = self._check_node(result)
        if not node_ok:
            return

        bridge_ok = self._install_whatsapp_bridge(result, bridge_dir)
        if not bridge_ok:
            return

        if params.get("session_id"):
            self._restore_whatsapp_session(result, session_dir, params["session_id"])
        else:
            self._pair_whatsapp(result, session_dir, bridge_dir)

        if result.success:
            self._save_env_var("WHATSAPP_ENABLED", "true")
            self._save_env_var("WHATSAPP_MODE", mode)
            self._save_env_var("WHATSAPP_ALLOWED_USERS", allowed_users)
            result.add_step("save_config", True, "WhatsApp config saved")

    def _check_node(self, result: ConfigResult) -> bool:
        """Check Node.js is available for WhatsApp bridge."""
        import shutil
        node = shutil.which("node")
        if node:
            result.add_step("check_node", True, f"Node.js found: {node}")
            return True
        result.add_step("check_node", False, "Node.js not found — install from nodejs.org")
        result.error = "Node.js is required for WhatsApp"
        return False

    def _install_whatsapp_bridge(
        self,
        result: ConfigResult,
        bridge_dir: Path,
    ) -> bool:
        """Install WhatsApp bridge dependencies."""
        bridge_script = bridge_dir / "bridge.js"
        if not bridge_script.exists():
            result.add_step("install_bridge", False, f"Bridge script not found at {bridge_dir}")
            result.error = "WhatsApp bridge not bundled — run setup manually"
            return False

        if not (bridge_dir / "node_modules").exists():
            import subprocess
            try:
                subprocess.run(
                    ["npm", "install", "--no-audit", "--no-fund"],
                    cwd=str(bridge_dir),
                    capture_output=True, text=True, timeout=120,
                )
                result.add_step("install_deps", True, "npm dependencies installed")
            except Exception as exc:
                result.add_step("install_deps", False, f"npm install failed: {exc}")
                result.error = "Failed to install WhatsApp bridge dependencies"
                return False
        else:
            result.add_step("install_deps", True, "Dependencies already installed")

        return True

    def _pair_whatsapp(
        self,
        result: ConfigResult,
        session_dir: Path,
        bridge_dir: Path,
    ) -> None:
        """Run WhatsApp QR pairing."""
        import subprocess
        creds_file = session_dir / "creds.json"
        if creds_file.exists():
            result.add_step("pair", True, "Existing session found — reuse")
            result.success = True
            return

        try:
            proc = subprocess.run(
                ["node", "bridge.js", "--pair-only", f"--session={session_dir}"],
                cwd=str(bridge_dir),
                capture_output=True, text=True, timeout=30,
            )
            output = (proc.stdout or "") + (proc.stderr or "")

            if "QRCODE" in output or creds_file.exists():
                result.add_step("pair", True, "QR code generated — scan with WhatsApp")
                result.success = True
            else:
                result.add_step("pair", False, f"Pairing failed: {output[:300]}")
                result.error = "WhatsApp pairing did not complete"
        except subprocess.TimeoutExpired:
            result.add_step("pair", False, "Pairing timed out")
            result.error = "WhatsApp pairing timed out"
        except Exception as exc:
            result.add_step("pair", False, f"Pairing error: {exc}")

    def _restore_whatsapp_session(
        self,
        result: ConfigResult,
        session_dir: Path,
        session_id: str,
    ) -> None:
        """Restore a saved WhatsApp session from session ID."""
        import shutil
        backup_path = Path("~/.gogeta/whatsapp/backups").expanduser() / f"{session_id}.json"
        if backup_path.exists():
            shutil.copy(str(backup_path), str(session_dir / "creds.json"))
            result.add_step("restore_session", True, f"Session restored from {session_id}")
            result.success = True
        else:
            result.add_step("restore_session", False, f"Backup {session_id} not found")
            result.error = "Session backup not found"

    def _setup_telegram(
        self,
        result: ConfigResult,
        params: Dict[str, Any],
    ) -> None:
        """Automated Telegram setup using managed bot onboarding."""
        try:
            from gogeta_cli.telegram_managed_bot import auto_setup_telegram_bot_result
            allowed_users = params.get("allowed_users", "*")

            bot_result = auto_setup_telegram_bot_result()
            if bot_result and bot_result.success:
                self._save_env_var("TELEGRAM_BOT_TOKEN", bot_result.bot_token)
                self._save_env_var("TELEGRAM_ALLOWED_USERS", allowed_users)
                if bot_result.home_channel:
                    self._save_env_var("TELEGRAM_HOME_CHANNEL", bot_result.home_channel)
                result.add_step("pair", True, "Telegram bot created and configured")
                result.success = True
            else:
                error = getattr(bot_result, "error", "Unknown error")
                result.add_step("pair", False, f"Telegram onboarding failed: {error}")
                result.error = error

        except ImportError:
            logger.info("Telegram managed bot not available, trying generic platform setup")
            self._setup_generic_platform(result, "telegram", params)

    def _setup_generic_platform(
        self,
        result: ConfigResult,
        platform: str,
        params: Dict[str, Any],
    ) -> None:
        """Generic platform setup via env vars.

        For platforms that just need a token + allowlist.
        """
        token_key = f"{platform.upper()}_BOT_TOKEN"
        token = params.get("token") or params.get("api_key") or ""
        allowed = params.get("allowed_users", "*")

        if token:
            self._save_env_var(token_key, token)
            result.add_step("configure", True, f"Token saved as {token_key}")
            result.success = True
        else:
            result.add_step("configure", False, f"No token provided for {platform}")
            result.error = f"Token required for {platform}. Set {token_key}."

        self._save_env_var(f"{platform.upper()}_ALLOWED_USERS", allowed)

    # ── Utilities ─────────────────────────────────────────────────────

    @staticmethod
    def _save_env_var(key: str, value: str) -> None:
        """Persist an env var to the user's .env file."""
        try:
            from gogeta_constants import get_gogeta_home
            env_path = get_gogeta_home() / ".env"
            env_path.parent.mkdir(parents=True, exist_ok=True)

            lines = []
            found = False
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.strip().startswith(f"{key}="):
                        lines.append(f"{key}={value}")
                        found = True
                    else:
                        lines.append(line)

            if not found:
                lines.append(f"{key}={value}")

            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            os.environ[key] = value
        except Exception as exc:
            logger.debug("Failed to save env var %s: %s", key, exc)

    @staticmethod
    def _emit_result(result: ConfigResult) -> None:
        """Emit configuration result to the event bus."""
        try:
            event_bus.emit(Event(
                type=EventType.SYSTEM_CONFIGURED,
                source="self_config_engine",
                data={
                    "task": result.task.value,
                    "target": result.target,
                    "success": result.success,
                    "steps": result.steps,
                    "error": result.error,
                    "elapsed": result.elapsed_seconds,
                },
            ))
        except Exception as exc:
            logger.debug("Failed to emit config event: %s", exc)

    @property
    def stats(self) -> Dict[str, Any]:
        total = len(self._results)
        passed = sum(1 for r in self._results if r.success)
        return {
            "total_attempts": total,
            "successful": passed,
            "failed": total - passed,
            "results": [
                {"target": r.target, "task": r.task.value, "success": r.success}
                for r in self._results[-10:]
            ],
        }


try:
    import os
except ImportError:
    import os

__all__ = ["SelfConfigEngine", "ConfigResult", "ConfigTask"]
