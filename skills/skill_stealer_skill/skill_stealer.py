import shutil
from pathlib import Path

# Common search paths for other AI agent skills
SEARCH_PATHS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".openclaw" / "skills",
    Path.home() / ".antigravity" / "skills"
]

class SkillStealer:
    def __init__(self, target_dir="skills"):
        self.target_dir = Path(target_dir)

    def scan(self):
        discovered = []
        for path in SEARCH_PATHS:
            if path.exists() and path.is_dir():
                for skill_folder in path.iterdir():
                    if skill_folder.is_dir():
                        discovered.append(skill_folder)
        return discovered

    def ingest(self, source_path):
        """Copies a skill folder and ensures it matches GOGETA standard."""
        skill_name = source_path.name
        dest_path = self.target_dir / f"{skill_name}_stolen"

        if dest_path.exists():
            return f"Skill {skill_name} already exists."

        try:
            shutil.copytree(source_path, dest_path)
            # Ensure SKILL.md exists
            skill_md = dest_path / "SKILL.md"
            if not skill_md.exists():
                self._create_stub_md(dest_path, skill_name)

            return f"Successfully stolen: {skill_name}"
        except Exception as e:
            return f"Error stealing {skill_name}: {e}"

    def _create_stub_md(self, folder, name):
        content = f"---\nname: {name}\ndescription: Stolen capability from external agent.\n---\n# {name}\n"
        with open(folder / "SKILL.md", "w") as f:
            f.write(content)

if __name__ == "__main__":
    stealer = SkillStealer()
    skills = stealer.scan()
    for s in skills:
        print(f"Discovered: {s}")
