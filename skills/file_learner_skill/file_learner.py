import os
import sys
from pathlib import Path

_GOGETA_HOME = Path(os.environ.get("GOGETA_HOME", str(Path.home() / ".gogeta")))

# Paths
MEMORY_DIR = _GOGETA_HOME / "memory"
PROJECTS_DIR = MEMORY_DIR / "projects"
DOMAINS_DIR = MEMORY_DIR / "domains"

def ensure_dirs():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    DOMAINS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_file(filepath):
    """Basic heuristic analysis of a file to extract patterns."""
    ext = os.path.splitext(filepath)[1].lower()
    patterns = []

    try:
        with open(filepath, encoding='utf-8') as f:
            lines = f.readlines()

        if ext == '.py':
            imports = [l.strip() for l in lines if l.startswith('import ') or l.startswith('from ')]  # noqa: E741
            if imports:
                patterns.append(f"Uses Python imports: {', '.join([i.split()[1] for i in imports[:5]])}...")

            # Check async usage
            if any('async def' in l for l in lines):  # noqa: E741
                patterns.append("Prefers asynchronous Python patterns (async/await).")

            # Check typing
            if any('->' in l or ':' in l for l in lines if 'def ' in l):  # noqa: E741
                patterns.append("Uses Python type hinting.")

        elif ext in ['.js', '.ts', '.tsx', '.jsx']:
            if any('React' in l or 'useState' in l for l in lines):  # noqa: E741
                patterns.append("Uses React framework for frontend.")
            if ext in ['.ts', '.tsx']:
                patterns.append("Prefers TypeScript for type safety.")

    except Exception as e:
        print(f"Could not read {filepath}: {e}")

    return patterns

def scan_target(target):
    ensure_dirs()
    target_path = Path(target)

    all_patterns = []
    if target_path.is_file():
        all_patterns.extend(analyze_file(target_path))
    elif target_path.is_dir():
        for root, _, files in os.walk(target_path):
            if '.git' in root or 'node_modules' in root or '__pycache__' in root:
                continue
            for file in files:
                filepath = Path(root) / file
                all_patterns.extend(analyze_file(filepath))

    if not all_patterns:
        print("No specific patterns found.")
        return

    # Deduplicate and summarize
    unique_patterns = list(set(all_patterns))

    # Save to domains memory
    memory_file = DOMAINS_DIR / "learned_patterns.md"
    existing_content = ""
    if memory_file.exists():
        existing_content = memory_file.read_text(encoding='utf-8')

    with open(memory_file, 'a', encoding='utf-8') as f:
        if not existing_content:
            f.write("# Learned Workspace Patterns\n\n")
        f.write("\n### Recent Scan Patterns:\n")
        for p in unique_patterns:
            if p not in existing_content:
                f.write(f"- {p}\n")

    print(f"Successfully learned {len(unique_patterns)} unique patterns and saved to {memory_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "scan":
        print("Usage: python file_learner.py scan <path>")
        sys.exit(1)

    scan_target(sys.argv[2])
