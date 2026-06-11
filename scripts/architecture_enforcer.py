#!/usr/bin/env python3
"""
Architecture enforcer for Gogeta/Gogeta Agent.

Validates layer dependency rules by scanning Python import statements.
Returns exit code 0 if clean, 1 if violations found.

Usage:
    python scripts/architecture_enforcer.py                          # scan all files
    python scripts/architecture_enforcer.py --report                 # generate full report
    python scripts/architecture_enforcer.py --ci                     # strict mode (CI)
    python scripts/architecture_enforcer.py --list-violations        # list-only mode
    python scripts/architecture_enforcer.py --json                   # JSON output
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Layer definitions: (directory/glob, layer_number, name)
# Layer 0 = innermost (foundation), Layer 9 = outermost (presentation)
# ---------------------------------------------------------------------------
LAYER_DEFS: List[Tuple[str, int, str]] = [
    # Layer 0: Foundation
    ("gogeta_constants.py", 0, "Foundation"),
    ("utils.py", 0, "Foundation"),
    ("gogeta_logging.py", 0, "Foundation"),
    ("gogeta_state.py", 0, "Foundation"),
    ("gogeta_time.py", 0, "Foundation"),
    # Layer 1: Tool Implementations
    ("tools/", 1, "Tool Implementations"),
    # Layer 2: Provider Registry
    ("providers/", 2, "Provider Registry"),
    ("plugins/model-providers/", 2, "Provider Registry (plugins)"),
    # Layer 3: Plugin System
    ("gogeta_cli/plugins.py", 3, "Plugin System"),
    ("gogeta_cli/middleware.py", 3, "Plugin System"),
    ("plugins/", 3, "Plugin System"),
    # Layer 4: Agent Core
    ("agent/", 4, "Agent Core"),
    # Layer 5: Orchestration
    ("run_agent.py", 5, "Orchestration"),
    ("cli.py", 5, "Orchestration"),
    ("model_tools.py", 5, "Orchestration"),
    ("batch_runner.py", 5, "Orchestration"),
    ("toolsets.py", 5, "Orchestration"),
    ("mcp_serve.py", 5, "Orchestration"),
    ("toolset_distributions.py", 5, "Orchestration"),
    ("trajectory_compressor.py", 5, "Orchestration"),
    ("mini_swe_runner.py", 5, "Orchestration"),
    # Layer 6: Cron
    ("cron/", 6, "Cron"),
    # Layer 7: Gateway
    ("gateway/", 7, "Gateway"),
    # Layer 8: CLI Application
    ("gogeta_cli/", 8, "CLI Application"),
    ("gogeta_cli/proxy/", 8, "CLI Application"),
    ("gogeta_cli/dashboard_auth/", 8, "CLI Application"),
    # Layer 9: Presentation / UI
    ("tui_gateway/", 9, "Presentation / UI"),
    ("acp_adapter/", 9, "Presentation / UI"),
    ("acp_registry/", 9, "Presentation / UI"),
]

# ---------------------------------------------------------------------------
# Specific prohibited import patterns
# These are checked IN ADDITION to layer ordering.
# ---------------------------------------------------------------------------
PROHIBITED_IMPORTS: List[Tuple[str, str, str]] = [
    # (source_pattern, import_pattern, reason)
    ("tools/", "agent.", "Tools must never import Agent Core"),
    ("tools/", "from agent", "Tools must never import Agent Core"),
    ("providers/", "agent.", "Provider Registry must never import Agent Core"),
    ("providers/", "from agent", "Provider Registry must never import Agent Core"),
    ("agent/", "gateway.", "Agent Core must never import Gateway"),
    ("agent/", "from gateway", "Agent Core must never import Gateway"),
    ("gateway/", "tools.", "Gateway must never import Tools directly"),
    ("gateway/", "from tools", "Gateway must never import Tools directly"),
    ("agent/", "tui_gateway.", "Agent Core must never import UI"),
    ("agent/", "from tui_gateway", "Agent Core must never import UI"),
    ("tools/", "gateway.", "Tools must never import Gateway"),
    ("tools/", "from gateway", "Tools must never import Gateway"),
    ("tools/", "run_agent", "Tools must never import run_agent"),
    ("tools/", "cli", "Tools must never import cli"),
]

# ---------------------------------------------------------------------------
# Non-project imports that are always allowed
# ---------------------------------------------------------------------------
STDLIB_PREFIXES = (
    "abc", "ast", "asyncio", "base64", "binascii", "builtins", "bz2",
    "calendar", "collections", "colorsys", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "csv", "ctypes",
    "dataclasses", "datetime", "decimal", "difflib", "dis",
    "email", "enum", "errno",
    "filecmp", "fileinput", "fnmatch", "fractions", "functools",
    "gc", "getopt", "getpass", "gettext", "glob", "grp",
    "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect",
    "io", "ipaddress",
    "json",
    "keyword",
    "linecache", "locale", "logging", "lzma",
    "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap",
    "modulefinder", "multiprocessing",
    "netrc", "nntplib", "numbers",
    "operator", "optparse",
    "os", "ossaudiodev",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath",
    "pprint", "profile", "pstats", "pty", "pwd",
    "py_compile", "pyclbr", "pydoc",
    "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource",
    "rlcompleter", "runpy",
    "sched", "secrets", "select", "selectors", "shelve", "shlex",
    "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr",
    "socket", "socketserver", "sqlite3", "ssl", "stat", "statistics",
    "string", "stringprep", "struct", "subprocess", "sunau",
    "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
    "test", "textwrap", "threading", "time", "timeit",
    "tkinter", "token", "tokenize", "trace", "traceback",
    "tracemalloc", "tty", "turtle", "turtledemo",
    "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid",
    "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound",
    "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib",
    # Third-party that's always acceptable
    "pydantic", "yaml", "ruamel", "jinja2", "markdown", "httpx",
    "requests", "openai", "dotenv", "rich", "tenacity", "prompt_toolkit",
    "croniter", "PIL", "pillow", "psutil", "pathspec",
    "curses", "fastapi", "uvicorn", "ptyprocess", "pywinpty",
)


def resolve_import(module_name: str) -> Optional[str]:
    """Resolve a dotted import name to a project-relative path prefix."""
    if not module_name:
        return None

    parts = module_name.split(".")

    # Check if it's a project-level module
    candidate = parts[0]
    for glob_pattern, layer, _ in LAYER_DEFS:
        # Normalize glob pattern to just the prefix
        prefix = glob_pattern.rstrip("/").rstrip(".py")
        if candidate == prefix or candidate.startswith(prefix + "."):
            return prefix
        # Handle tools.environments, tools.computer_use, etc.
        if len(parts) >= 2:
            two_part = ".".join(parts[:2])
            if two_part == prefix or two_part.startswith(prefix + "."):
                return prefix

    return None


def get_layer_for_file(file_path: Path) -> Optional[int]:
    """Determine which layer a file belongs to."""
    rel = file_path.relative_to(REPO_ROOT)
    rel_str = str(rel.as_posix())

    for glob_pattern, layer, _ in LAYER_DEFS:
        if glob_pattern.endswith(".py"):
            if rel_str == glob_pattern:
                return layer
        else:
            # Directory pattern
            if rel_str.startswith(glob_pattern) or rel_str.startswith(glob_pattern.rstrip("/")):
                return layer

    return None


def get_layer_name_for_file(file_path: Path) -> str:
    """Get human-readable layer name."""
    rel = file_path.relative_to(REPO_ROOT)
    rel_str = str(rel.as_posix())

    for glob_pattern, layer, name in LAYER_DEFS:
        if glob_pattern.endswith(".py"):
            if rel_str == glob_pattern:
                return name
        else:
            if rel_str.startswith(glob_pattern) or rel_str.startswith(glob_pattern.rstrip("/")):
                return name

    return "Unknown"


def get_file_layer_label(file_path: Path) -> str:
    """Get short layer label for a file."""
    layer = get_layer_for_file(file_path)
    name = get_layer_name_for_file(file_path)
    if layer is not None:
        return f"L{layer}"
    return "?"


def is_prohibited_import(file_path: Path, imported_module: str) -> Optional[Tuple[str, str]]:
    """Check if an import is specifically prohibited."""
    rel = str(file_path.relative_to(REPO_ROOT).as_posix())

    for src_pattern, imp_pattern, reason in PROHIBITED_IMPORTS:
        if rel.startswith(src_pattern) or rel == src_pattern:
            if imported_module.startswith(imp_pattern):
                return (imported_module, reason)
    return None


def extract_imports(file_path: Path) -> List[str]:
    """Extract all top-level import module names from a Python file."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"  [WARN] Cannot read {file_path}: {e}", file=sys.stderr)
        return imports

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        print(f"  [WARN] Syntax error in {file_path}: {e}", file=sys.stderr)
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
            # Also handle `from . import X` and `from .module import X`
            # For relative imports, we track the level
            elif node.level:
                imports.append(f".<relative level={node.level}>")

    # Remove stdlib and known third-party
    result = []
    for mod in imports:
        top_level = mod.split(".")[0]
        if top_level not in STDLIB_PREFIXES and not mod.startswith("."):
            result.append(mod)

    return result


def is_test_file(file_path: Path) -> bool:
    """Check if a file is a test file."""
    rel = str(file_path.relative_to(REPO_ROOT).as_posix())
    return rel.startswith("tests/") or rel.startswith("test_") or "_test" in rel


def is_skill_file(file_path: Path) -> bool:
    """Check if a file is a skill file."""
    rel = str(file_path.relative_to(REPO_ROOT).as_posix())
    return rel.startswith("skills/") or rel.startswith("optional-skills/")


def scan_file(
    file_path: Path, ci_mode: bool = False
) -> Tuple[List[Dict], List[Dict]]:
    """
    Scan a single file for architecture violations.

    Returns (layer_violations, prohibited_import_violations).
    """
    violations = []
    prohibited = []

    file_layer = get_layer_for_file(file_path)
    if file_layer is None:
        return violations, prohibited

    imports = extract_imports(file_path)

    for imp in imports:
        # Check specific prohibited imports first
        result = is_prohibited_import(file_path, imp)
        if result:
            prohibited.append({
                "file": str(file_path.relative_to(REPO_ROOT)),
                "layer": file_layer,
                "import": imp,
                "source": result[0],
                "reason": result[1],
            })
            continue

        # Resolve to project module
        resolved = resolve_import(imp)
        if resolved is None:
            continue

        # Find the layer of the imported module
        imported_layer = None
        for glob_pattern, layer, _ in LAYER_DEFS:
            prefix = glob_pattern.rstrip("/").rstrip(".py")
            if resolved == prefix or resolved.startswith(prefix + "."):
                imported_layer = layer
                break

        if imported_layer is None:
            continue

        # Check layer direction (allow same layer)
        # Lower layer (smaller number) must not import from higher layer (larger number)
        if imported_layer > file_layer:
            # Check if it's a lazy import (which may be allowed)
            if _is_lazy_import(file_path, imp):
                # Lazy imports between certain layers are allowed
                if file_layer == 4 and imported_layer >= 3:
                    # Agent core lazy-importing plugin system is allowed
                    continue
                if file_layer == 5 and imported_layer >= 4:
                    continue

            violations.append({
                "file": str(file_path.relative_to(REPO_ROOT)),
                "layer": file_layer,
                "layer_name": get_layer_name_for_file(file_path),
                "imports": imp,
                "import_layer": imported_layer,
                "import_layer_name": get_layer_name_for_file(
                    REPO_ROOT / resolved.replace(".", "/")
                ) if resolved else "Unknown",
                "detail": f"L{file_layer} ({get_layer_name_for_file(file_path)}) must not import L{imported_layer} ({get_layer_name_for_file(REPO_ROOT / resolved.replace('.', '/')) if resolved else 'Unknown'})",
            })

    return violations, prohibited


def _is_lazy_import(file_path: Path, import_name: str) -> bool:
    """Heuristic: check if an import is inside a function (lazy)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    # Simple heuristic: look for `import X` inside a function body
    # by checking indentation
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            # If the line is indented with leading whitespace (tab or spaces),
            # it's likely inside a function or class
            if line.startswith((" ", "\t")) and import_name in stripped:
                return True

    return False


def get_all_python_files() -> List[Path]:
    """Get all project Python files to scan, excluding tests, skills, and build artifacts."""
    files = []
    exclude_dirs = {
        "tests", "skills", "optional-skills", "ui-tui", "website",
        "node_modules", "__pycache__", ".git", ".venv", "venv",
        "env", "build", "dist", "*.egg-info", ".mypy_cache",
        ".ruff_cache", ".pytest_cache", "apps/desktop",
    }

    for root, dirs, filenames in os.walk(str(REPO_ROOT)):
        rel_root = os.path.relpath(root, str(REPO_ROOT))
        rel_parts = rel_root.replace("\\", "/").split("/")

        # Skip excluded directories
        if any(p in exclude_dirs for p in rel_parts):
            continue

        for f in filenames:
            if f.endswith(".py"):
                files.append(Path(root) / f)

    return sorted(files)


def scan_all(ci_mode: bool = False) -> Tuple[List[Dict], List[Dict], int]:
    """Scan all project files. Returns (layer_violations, prohibited_violations, file_count)."""
    all_layer_violations = []
    all_prohibited_violations = []
    file_count = 0

    files = get_all_python_files()
    for fp in files:
        file_count += 1
        layer_v, prohibited_v = scan_file(fp, ci_mode=ci_mode)
        all_layer_violations.extend(layer_v)
        all_prohibited_violations.extend(prohibited_v)

    return all_layer_violations, all_prohibited_violations, file_count


def print_report(
    layer_violations: List[Dict],
    prohibited_violations: List[Dict],
    file_count: int,
    json_output: bool = False,
):
    """Print a human-readable or JSON report."""
    if json_output:
        print(json.dumps({
            "file_count": file_count,
            "layer_violations": layer_violations,
            "prohibited_violations": prohibited_violations,
            "total_violations": len(layer_violations) + len(prohibited_violations),
            "status": "FAIL" if layer_violations or prohibited_violations else "PASS",
        }, indent=2))
        return

    total = len(layer_violations) + len(prohibited_violations)

    print(f"{'=' * 72}")
    print(f"  Gogeta Architecture Enforcer")
    print(f"{'=' * 72}")
    print(f"  Files scanned:  {file_count}")
    print(f"  Violations:     {total}")
    print()

    if prohibited_violations:
        print(f"{'─' * 72}")
        print(f"  PROHIBITED IMPORT VIOLATIONS ({len(prohibited_violations)})")
        print(f"{'─' * 72}")
        for v in sorted(prohibited_violations, key=lambda x: (x["file"], x["import"])):
            print(f"  [{v['layer']}] {v['file']}")
            print(f"       imports {v['import']}")
            print(f"       REASON: {v['reason']}")
            print()

    if layer_violations:
        print(f"{'─' * 72}")
        print(f"  LAYER VIOLATIONS ({len(layer_violations)})")
        print(f"{'─' * 72}")
        for v in sorted(layer_violations, key=lambda x: (x["layer"], x["file"], x["imports"])):
            print(f"  [{v['layer']}] {v['file']}")
            print(f"       imports {v['imports']} (Layer {v['import_layer']})")
            print(f"       {v.get('detail', 'Lower layer must not import from higher layer')}")
            print()

    if total == 0:
        print(f"  ✓ All architecture rules pass.")
    else:
        print(f"  ✗ {total} violation(s) found.")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Gogeta Architecture Enforcer — validate layer dependency rules"
    )
    parser.add_argument("--report", action="store_true", help="Print full architecture report")
    parser.add_argument("--ci", action="store_true", help="CI mode (strict)")
    parser.add_argument("--list-violations", action="store_true", help="List-only mode")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--file", type=str, help="Scan a single file only")

    args = parser.parse_args()

    if args.file:
        fp = Path(args.file)
        if not fp.exists():
            print(f"File not found: {fp}", file=sys.stderr)
            sys.exit(1)
        layer_v, prohibited_v = scan_file(fp, ci_mode=args.ci)
        file_count = 1
    else:
        layer_v, prohibited_v, file_count = scan_all(ci_mode=args.ci)

    if args.json:
        print_report(layer_v, prohibited_v, file_count, json_output=True)
    elif args.report or args.list_violations:
        print_report(layer_v, prohibited_v, file_count)
    else:
        total = len(layer_v) + len(prohibited_v)
        print(f"Scanned {file_count} files — {total} violation(s)")
        if total:
            for v in prohibited_v:
                print(f"  ✗ {v['file']}: {v['reason']} ({v['import']})")
            for v in layer_v:
                detail = v.get("detail", f"L{v['layer']} imports L{v['import_layer']}")
                print(f"  ✗ {v['file']}: {detail}")

    # Return exit code
    if layer_v or prohibited_v:
        sys.exit(1)


if __name__ == "__main__":
    main()
