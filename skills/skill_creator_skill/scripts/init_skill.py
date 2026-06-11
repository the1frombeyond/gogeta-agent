import sys
from pathlib import Path


def init_skill(name, base_path="skills"):
    skill_dir = Path(base_path) / f"{name.replace(' ', '_').lower()}_skill"
    if skill_dir.exists():
        print(f"Error: Skill {name} already exists at {skill_dir}")
        return

    # Create directory structure
    for sub in ["scripts", "references", "assets"]:
        (skill_dir / sub).mkdir(parents=True, exist_ok=True)

    # Create SKILL.md template
    skill_md_content = f"""---
name: {name.lower()}
description: Enter a clear description here for discovery.
version: 1.0.0
---

# {name} Skill

Instructions for using this skill.

## Workflow
1. Step one
2. Step two

## Scripts
- No scripts yet.
"""
    with open(skill_dir / "SKILL.md", "w") as f:
        f.write(skill_md_content)

    print(f"Skill {name} initialized successfully at {skill_dir}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        init_skill(sys.argv[1])
    else:
        print("Usage: python init_skill.py <skill-name>")
