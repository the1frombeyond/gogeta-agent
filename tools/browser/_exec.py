import json
import logging
import os
import shutil
import subprocess

from pathlib import Path

from tools.browser._state import (
    _active_sessions,
    _cleanup_lock,
    _cached_agent_browser,
    _agent_browser_resolved,
    _EMPTY_OK_COMMANDS,
    BROWSER_SESSION_INACTIVITY_TIMEOUT,
    logger,
)
from tools.browser._config import (
    _merge_browser_path,
    _get_command_timeout,
    _socket_safe_tmpdir,
)
from tools.browser._cloud import _is_local_mode, _is_local_backend
from tools.browser._session import _get_session_info
from tools.browser._engine import (
    _get_browser_engine,
    _lightpanda_fallback_reason,
    _using_lightpanda_engine,
    _annotate_lightpanda_fallback,
)
from tools.browser._requirements import _chromium_installed, _running_in_docker

logger = logging.getLogger(__name__)


def _browser_install_hint() -> str:
    from gogeta_constants import is_termux as _is_termux_environment
    if _is_termux_environment():
        return "npm install -g agent-browser && agent-browser install"
    return "npm install -g agent-browser && agent-browser install --with-deps"


def _requires_real_termux_browser_install(browser_cmd: str) -> bool:
    from gogeta_constants import is_termux as _is_termux_environment
    return _is_termux_environment() and _is_local_mode() and browser_cmd.strip() == "npx agent-browser"


def _termux_browser_install_error() -> str:
    return (
        "Local browser automation on Termux cannot rely on the bare npx fallback. "
        f"Install agent-browser explicitly first: {_browser_install_hint()}"
    )


def _find_agent_browser() -> str:
    global _cached_agent_browser, _agent_browser_resolved
    if _agent_browser_resolved:
        if _cached_agent_browser is None:
            raise FileNotFoundError(
                "agent-browser CLI not found (cached). Install it with: "
                f"{_browser_install_hint()}\n"
                "Or run 'npm install' in the repo root to install locally.\n"
            )
        return _cached_agent_browser
    _agent_browser_resolved = True
    ab = shutil.which("agent-browser")
    if ab:
        _cached_agent_browser = ab
        return ab
    import subprocess
    npx = shutil.which("npx")
    if npx:
        try:
            result = subprocess.run(
                [npx, "agent-browser", "--version"],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PATH": _merge_browser_path(os.environ.get("PATH", ""))},
            )
            if result.returncode == 0:
                _cached_agent_browser = "npx agent-browser"
                return _cached_agent_browser
        except (subprocess.TimeoutExpired, OSError):
            pass
    raise FileNotFoundError(
        "agent-browser CLI not found. Install it with: "
        f"{_browser_install_hint()}\n"
    )


def _extract_screenshot_path_from_text(text: str) -> str | None:
    if not text:
        return None
    import re
    patterns = [
        r"Screenshot saved to ['\"](?P<path>/[^'\"]+?\.png)['\"]",
        r"Screenshot saved to (?P<path>/\S+?\.png)(?:\s|$)",
        r"(?P<path>/\S+?\.png)(?:\s|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            path = match.group("path").strip().strip("'\"")
            if path:
                return path
    return None


def _maybe_start_recording(task_id: str):
    from tools.browser._state import _recording_sessions
    if task_id in _recording_sessions:
        return
    _recording_sessions.add(task_id)
    _run_browser_command(task_id, "record", ["start"])


def _maybe_stop_recording(task_id: str):
    from tools.browser._state import _recording_sessions
    if task_id not in _recording_sessions:
        return
    _recording_sessions.discard(task_id)
    _run_browser_command(task_id, "record", ["stop"])


def _run_chrome_fallback_command(
    task_id: str,
    command: str,
    args: list[str],
    timeout: int,
) -> dict:
    import uuid as _uuid
    from tools.browser._config import _merge_browser_path, _socket_safe_tmpdir
    from tools.browser._session import _get_session_info
    from tools.browser._requirements import _chromium_installed, _running_in_docker
    from tools.browser._state import BROWSER_SESSION_INACTIVITY_TIMEOUT

    url_result = _run_browser_command(
        task_id, "eval", ["window.location.href"], timeout=10, _engine_override="auto"
    )
    current_url = None
    if url_result.get("success"):
        current_url = url_result.get("data", {}).get("result", "").strip().strip('"').strip("'")
    if not current_url:
        logger.warning("Chrome fallback: could not determine current URL from LP session")
        return {"success": False, "error": "Chrome fallback failed: could not determine current URL"}
    tmp_session = f"h_cfb_{_uuid.uuid4().hex[:8]}"
    try:
        browser_cmd = _find_agent_browser()
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    if not _chromium_installed():
        if _running_in_docker():
            hint = (
                "Chrome fallback requires Chromium, but it is missing. "
                "You're running in Docker — pull the latest image: "
                "docker pull ghcr.io/gogeta/gogeta-agent:latest"
            )
        else:
            hint = (
                "Chrome fallback requires Chromium, but it is missing. Install it with: "
                "npx agent-browser install --with-deps "
                "(or: npx playwright install --with-deps chromium)"
            )
        return {"success": False, "error": hint}
    if browser_cmd == "npx agent-browser":
        _npx_bin = shutil.which("npx") or "npx"
        cmd_prefix = [_npx_bin, "agent-browser"]
    else:
        cmd_prefix = [browser_cmd]
    base_args = cmd_prefix + ["--engine", "chrome", "--session", tmp_session, "--json"]
    task_socket_dir = os.path.join(_socket_safe_tmpdir(), f"agent-browser-{tmp_session}")
    os.makedirs(task_socket_dir, mode=0o700, exist_ok=True)
    browser_env = {**os.environ, "AGENT_BROWSER_SOCKET_DIR": task_socket_dir}
    browser_env["PATH"] = _merge_browser_path(browser_env.get("PATH", ""))
    if "AGENT_BROWSER_IDLE_TIMEOUT_MS" not in browser_env:
        browser_env["AGENT_BROWSER_IDLE_TIMEOUT_MS"] = str(BROWSER_SESSION_INACTIVITY_TIMEOUT * 1000)

    def _run_tmp(cmd: str, cmd_args: list[str]) -> dict:
        full = base_args + [cmd] + cmd_args
        stdout_path = os.path.join(task_socket_dir, f"_stdout_{cmd}")
        stderr_path = os.path.join(task_socket_dir, f"_stderr_{cmd}")
        stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            _popen_extra: dict = {}
            if os.name == "nt":
                _CREATE_NO_WINDOW = 0x08000000
                _popen_extra["creationflags"] = _CREATE_NO_WINDOW
                _popen_extra["close_fds"] = True
                _si = subprocess.STARTUPINFO()
                _si.dwFlags |= subprocess.STARTF_USESTDHANDLES
                _popen_extra["startupinfo"] = _si
            proc = subprocess.Popen(
                full, stdout=stdout_fd, stderr=stderr_fd,
                stdin=subprocess.DEVNULL, env=browser_env,
                **_popen_extra,
            )
        finally:
            os.close(stdout_fd)
            os.close(stderr_fd)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return {"success": False, "error": f"Chrome fallback '{cmd}' timed out"}
        try:
            with open(stdout_path, "r", encoding="utf-8") as f:
                stdout = f.read().strip()
            if stdout:
                return json.loads(stdout.split("\n")[-1])
        except Exception as exc:
            logger.debug("Chrome fallback tmp cmd '%s' error: %s", cmd, exc)
        finally:
            for pth in (stdout_path, stderr_path):
                try:
                    os.unlink(pth)
                except OSError:
                    pass
        return {"success": False, "error": f"Chrome fallback '{cmd}' failed"}

    try:
        nav = _run_tmp("open", [current_url])
        if not nav.get("success"):
            logger.warning("Chrome fallback: navigate failed: %s", nav.get("error"))
            return {"success": False, "error": f"Chrome fallback navigate failed: {nav.get('error')}"}
        return _run_tmp(command, args)
    finally:
        try:
            _run_tmp("close", [])
        except Exception:
            pass
        import shutil as _shutil
        _shutil.rmtree(task_socket_dir, ignore_errors=True)


def _chrome_fallback_screenshot(task_id: str, args: list[str], timeout: int) -> dict:
    return _run_chrome_fallback_command(task_id, "screenshot", args, timeout)


def _run_browser_command(
    task_id: str,
    command: str,
    args: list[str] | None = None,
    timeout: int | None = None,
    _engine_override: str | None = None,
) -> dict:
    if timeout is None:
        timeout = _get_command_timeout()
    args = args or []
    try:
        browser_cmd = _find_agent_browser()
    except FileNotFoundError as e:
        logger.warning("agent-browser CLI not found: %s", e)
        return {"success": False, "error": str(e)}
    if _requires_real_termux_browser_install(browser_cmd):
        error = _termux_browser_install_error()
        logger.warning("browser command blocked on Termux: %s", error)
        return {"success": False, "error": error}
    if _is_local_mode() and not _chromium_installed() and _get_browser_engine() != "lightpanda":
        if _running_in_docker():
            hint = (
                "Chromium browser is missing. You're running in Docker — pull "
                "the latest image to get the bundled Chromium: "
                "docker pull ghcr.io/gogeta/gogeta-agent:latest"
            )
        else:
            hint = (
                "Chromium browser is missing. Install it with: "
                "npx agent-browser install --with-deps "
                "(or: npx playwright install --with-deps chromium)"
            )
        logger.warning("browser command blocked: %s", hint)
        return {"success": False, "error": hint}
    from tools.interrupt import is_interrupted
    if is_interrupted():
        return {"success": False, "error": "Interrupted"}
    try:
        session_info = _get_session_info(task_id)
    except Exception as e:
        logger.warning("Failed to create browser session for task=%s: %s", task_id, e)
        return {"success": False, "error": f"Failed to create browser session: {str(e)}"}
    if session_info.get("cdp_url"):
        backend_args = ["--cdp", session_info["cdp_url"]]
    else:
        backend_args = ["--session", session_info["session_name"]]
    engine = _engine_override or _get_browser_engine()
    if engine != "auto":
        try:
            from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
            is_camofox = _is_camofox_mode()
        except ImportError:
            is_camofox = False
        if not is_camofox and not session_info.get("cdp_url"):
            backend_args += ["--engine", engine]
    if browser_cmd == "npx agent-browser":
        _npx_bin = shutil.which("npx") or "npx"
        cmd_prefix = [_npx_bin, "agent-browser"]
    else:
        cmd_prefix = [browser_cmd]
    cmd_parts = cmd_prefix + backend_args + ["--json", command] + args
    try:
        task_socket_dir = os.path.join(
            _socket_safe_tmpdir(),
            f"agent-browser-{session_info['session_name']}"
        )
        os.makedirs(task_socket_dir, mode=0o700, exist_ok=True)
        from tools.browser.cleanup import _write_owner_pid
        _write_owner_pid(task_socket_dir, session_info['session_name'])
        logger.debug("browser cmd=%s task=%s socket_dir=%s (%d chars)",
                     command, task_id, task_socket_dir, len(task_socket_dir))
        browser_env = {**os.environ}
        browser_env["PATH"] = _merge_browser_path(browser_env.get("PATH", ""))
        browser_env["AGENT_BROWSER_SOCKET_DIR"] = task_socket_dir
        if "AGENT_BROWSER_IDLE_TIMEOUT_MS" not in browser_env:
            idle_ms = str(BROWSER_SESSION_INACTIVITY_TIMEOUT * 1000)
            browser_env["AGENT_BROWSER_IDLE_TIMEOUT_MS"] = idle_ms
        if (
            "AGENT_BROWSER_ARGS" not in browser_env
            and "AGENT_BROWSER_CHROME_FLAGS" not in browser_env
        ):
            _needs_sandbox_bypass = False
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                _needs_sandbox_bypass = True
                logger.debug("browser: running as root — injecting --no-sandbox")
            else:
                _userns_restrict = "/proc/sys/kernel/apparmor_restrict_unprivileged_userns"
                try:
                    with open(_userns_restrict, encoding="utf-8") as _f:
                        if _f.read().strip() == "1":
                            _needs_sandbox_bypass = True
                            logger.debug(
                                "browser: AppArmor userns restrictions detected — injecting --no-sandbox"
                            )
                except OSError:
                    pass
            if _needs_sandbox_bypass:
                browser_env["AGENT_BROWSER_ARGS"] = (
                    "--no-sandbox,--disable-dev-shm-usage"
                )
        stdout_path = os.path.join(task_socket_dir, f"_stdout_{command}")
        stderr_path = os.path.join(task_socket_dir, f"_stderr_{command}")
        stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            _popen_extra: dict = {}
            if os.name == "nt":
                _CREATE_NO_WINDOW = 0x08000000
                _popen_extra["creationflags"] = _CREATE_NO_WINDOW
                _popen_extra["close_fds"] = True
                _si = subprocess.STARTUPINFO()
                _si.dwFlags |= subprocess.STARTF_USESTDHANDLES
                _popen_extra["startupinfo"] = _si
            proc = subprocess.Popen(
                cmd_parts,
                stdout=stdout_fd, stderr=stderr_fd,
                stdin=subprocess.DEVNULL, env=browser_env,
                **_popen_extra,
            )
        finally:
            os.close(stdout_fd)
            os.close(stderr_fd)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            logger.warning("browser '%s' timed out after %ds (task=%s, socket_dir=%s)",
                           command, timeout, task_id, task_socket_dir)
            result = {"success": False, "error": f"Command timed out after {timeout} seconds"}
        else:
            with open(stdout_path, "r", encoding="utf-8") as f:
                stdout = f.read()
            with open(stderr_path, "r", encoding="utf-8") as f:
                stderr = f.read()
            returncode = proc.returncode
            for p in (stdout_path, stderr_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
            if stderr and stderr.strip():
                level = logging.WARNING if returncode != 0 else logging.DEBUG
                logger.log(level, "browser '%s' stderr: %s", command, stderr.strip()[:500])
            stdout_text = stdout.strip()
            if not stdout_text and returncode == 0 and command not in _EMPTY_OK_COMMANDS:
                logger.warning("browser '%s' returned empty output (rc=0)", command)
                result = {"success": False, "error": f"Browser command '{command}' returned no output"}
            elif stdout_text:
                try:
                    parsed = json.loads(stdout_text)
                    if command == "snapshot" and parsed.get("success"):
                        snap_data = parsed.get("data", {})
                        if not snap_data.get("snapshot") and not snap_data.get("refs"):
                            logger.warning(
                                "snapshot returned empty content. "
                                "Possible stale daemon or CDP connection issue. "
                                "returncode=%s", returncode
                            )
                    result = parsed
                except json.JSONDecodeError:
                    raw = stdout_text[:2000]
                    logger.warning("browser '%s' returned non-JSON output (rc=%s): %s",
                                   command, returncode, raw[:500])
                    if command == "screenshot":
                        stderr_text = (stderr or "").strip()
                        combined_text = "\n".join(part for part in [stdout_text, stderr_text] if part)
                        recovered_path = _extract_screenshot_path_from_text(combined_text)
                        if recovered_path and Path(recovered_path).exists():
                            logger.info("browser 'screenshot' recovered file from non-JSON output: %s", recovered_path)
                            result = {
                                "success": True,
                                "data": {"path": recovered_path, "raw": raw},
                            }
                        else:
                            result = {
                                "success": False,
                                "error": f"Non-JSON output from agent-browser for '{command}': {raw}"
                            }
                    else:
                        result = {
                            "success": False,
                            "error": f"Non-JSON output from agent-browser for '{command}': {raw}"
                        }
            elif returncode != 0:
                error_msg = stderr.strip() if stderr else f"Command failed with code {returncode}"
                logger.warning("browser '%s' failed (rc=%s): %s", command, returncode, error_msg[:300])
                result = {"success": False, "error": error_msg}
            else:
                result = {"success": True, "data": {}}
    except Exception as e:
        logger.warning("browser '%s' exception: %s", command, e, exc_info=True)
        result = {"success": False, "error": str(e)}
    fallback_reason = _lightpanda_fallback_reason(engine, command, result)
    if fallback_reason:
        logger.info(
            "Lightpanda fallback: retrying '%s' with Chrome (task=%s): %s",
            command, task_id, fallback_reason,
        )
        if command == "screenshot":
            fallback_result = _chrome_fallback_screenshot(task_id, args or [], timeout)
        else:
            fallback_result = _run_chrome_fallback_command(task_id, command, args, timeout)
        return _annotate_lightpanda_fallback(fallback_result, fallback_reason)
    return result
