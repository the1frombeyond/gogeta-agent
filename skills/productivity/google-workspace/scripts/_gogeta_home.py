"""Resolve GOGETA_HOME for standalone skill scripts.

Skill scripts may run outside the Gogeta process (e.g. system Python,
nix env, CI) where ``gogeta_constants`` is not importable.  This module
provides the same ``get_gogeta_home()`` and ``display_gogeta_home()``
contracts as ``gogeta_constants`` without requiring it on ``sys.path``.

When ``gogeta_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``gogeta_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``GOGETA_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from gogeta_constants import display_gogeta_home as display_gogeta_home
    from gogeta_constants import get_gogeta_home as get_gogeta_home
except (ModuleNotFoundError, ImportError):

    def get_gogeta_home() -> Path:
        """Return the Gogeta home directory (default: ~/.gogeta).

        Mirrors ``gogeta_constants.get_gogeta_home()``."""
        val = os.environ.get("GOGETA_HOME", "").strip()
        return Path(val) if val else Path.home() / ".gogeta"

    def display_gogeta_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``gogeta_constants.display_gogeta_home()``."""
        home = get_gogeta_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
