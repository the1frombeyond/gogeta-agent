import logging
import os
import shutil
import subprocess

from tools.browser._state import logger

logger = logging.getLogger(__name__)


def _chromium_search_roots() -> list[str]:
    paths = []
    if shutil.which("chromium"):
        paths.append(shutil.which("chromium"))
    if shutil.which("chromium-browser"):
        paths.append(shutil.which("chromium-browser"))
    if shutil.which("google-chrome"):
        paths.append(shutil.which("google-chrome"))
    if shutil.which("google-chrome-stable"):
        paths.append(shutil.which("google-chrome-stable"))
    if shutil.which("chrome"):
        paths.append(shutil.which("chrome"))
    if os.path.isdir("/opt/homebrew/bin"):
        for name in ("chromium", "google-chrome", "google-chrome-stable", "chrome", "chromium-browser"):
            candidate = f"/opt/homebrew/bin/{name}"
            if os.path.isfile(candidate):
                paths.append(candidate)
    if os.path.isdir("/usr/bin"):
        for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
            candidate = f"/usr/bin/{name}"
            if os.path.isfile(candidate):
                paths.append(candidate)
    return paths


def _chromium_installed() -> bool:
    return bool(_chromium_search_roots())


def _running_in_docker() -> bool:
    try:
        if os.path.isfile("/.dockerenv"):
            return True
        with open("/proc/1/cgroup", encoding="utf-8") as f:
            return "docker" in f.read()
    except (FileNotFoundError, OSError):
        return False


def check_browser_requirements() -> bool:
    try:
        if shutil.which("agent-browser"):
            return True
        npx = shutil.which("npx")
        if npx is None:
            if shutil.which("node") or shutil.which("nodejs"):
                return shutil.which("npm") is not None
            return False
        result = subprocess.run(
            [npx, "agent-browser", "--version"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_browser_vision_requirements() -> bool:
    return bool(os.getenv("AUXILIARY_VISION_MODEL", "").strip())
