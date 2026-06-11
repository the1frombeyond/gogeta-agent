import os
from pathlib import Path

_GOGETA_HOME = Path(os.environ.get("GOGETA_HOME", str(Path.home() / ".gogeta")))
MEMORY_BASE = _GOGETA_HOME / "memory"

def get_stats():
    stats = {
        "HOT": 0,
        "WARM_PROJECTS": 0,
        "WARM_DOMAINS": 0,
        "COLD": 0
    }

    # HOT
    hot_file = MEMORY_BASE / "memory.md"
    if hot_file.exists():
        stats["HOT"] = len(hot_file.read_text().splitlines())

    # WARM
    stats["WARM_PROJECTS"] = len(list((MEMORY_BASE / "projects").iterdir()))
    stats["WARM_DOMAINS"] = len(list((MEMORY_BASE / "domains").iterdir()))

    # COLD
    stats["COLD"] = len(list((MEMORY_BASE / "archive").iterdir()))

    print("📊 Self-Improving Memory Stats")
    print(f"HOT (memory.md): {stats['HOT']} lines")
    print(f"WARM (projects/): {stats['WARM_PROJECTS']} files")
    print(f"WARM (domains/): {stats['WARM_DOMAINS']} files")
    print(f"COLD (archive/): {stats['COLD']} files")

if __name__ == "__main__":
    get_stats()
