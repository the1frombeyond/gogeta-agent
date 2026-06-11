#!/usr/bin/env python3
"""CI-friendly architecture check wrapper.

Thin wrapper around scripts/architecture_enforcer.py that formats output
suitable for CI pipeline summaries and PR comments.

Usage:
    python scripts/check_architecture.py              # normal check (exit 1 on violations)
    python scripts/check_architecture.py --advisory   # non-blocking advisory mode
    python scripts/check_architecture.py --ci         # strict CI mode
"""

import subprocess
import sys
from pathlib import Path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CI-friendly architecture check wrapper")
    parser.add_argument("--advisory", action="store_true", help="Non-blocking advisory mode")
    parser.add_argument("--ci", action="store_true", help="Strict CI mode")
    parser.add_argument("--json", action="store_true", help="Produce JSON output for CI parsing")
    args = parser.parse_args()

    enforcer = Path(__file__).resolve().parent / "architecture_enforcer.py"
    cmd = [sys.executable, str(enforcer), "--json"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    import json
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        print("Architecture check: could not parse enforcer output", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(0 if args.advisory else 1)
        return

    total = data["total_violations"]
    file_count = data["file_count"]
    status = data["status"]

    # Print CI-friendly summary
    print(f"::group::Architecture Check")
    print(f"Files scanned: {file_count}")
    print(f"Total violations: {total}")
    print(f"Status: {status}")
    print()

    for v in data.get("prohibited_violations", []):
        print(f"::error file={v['file']},title=Architecture Violation::{v['reason']} ({v['import']})")

    for v in data.get("layer_violations", []):
        print(f"::warning file={v['file']},title=Layer Violation::L{v['layer']} imports L{v['import_layer']} ({v['imports']})")

    print()

    if data.get("prohibited_violations"):
        print("Prohibited import violations:")
        for v in data["prohibited_violations"]:
            print(f"  [ERR] {v['file']}: {v['reason']}")
            print(f"        Import: {v['import']}")
        print()

    if data.get("layer_violations"):
        print("Layer violations:")
        for v in data["layer_violations"]:
            print(f"  [WRN] {v['file']}: L{v['layer']} ({v['layer_name']}) imports {v['imports']} (L{v['import_layer']})")
        print()

    if total == 0:
        print("[OK] All architecture rules pass.")
    else:
        print(f"[FAIL] {total} violation(s) found.")

    print("::endgroup::")

    if args.advisory:
        sys.exit(0)
    else:
        # Also allow violations to pass if none are PROHIBITED type (only layer warnings)
        has_prohibited = len(data.get("prohibited_violations", [])) > 0
        if args.ci:
            sys.exit(1 if total > 0 else 0)
        else:
            sys.exit(1 if has_prohibited else 0)


if __name__ == "__main__":
    main()
