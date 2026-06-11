"""OpenClaw migration tool — import settings, memories, skills, API keys from ~/.openclaw"""

import json
import os
import shutil
from pathlib import Path

GOGETA_HOME = Path(os.environ.get("GOGETA_HOME", str(Path.home() / ".gogeta")))
OPENCLAW_HOME = Path.home() / ".openclaw"


def detect_openclaw() -> bool:
    return OPENCLAW_HOME.exists()


def preview() -> dict:
    """Dry-run: return what would be migrated without writing anything."""
    if not detect_openclaw():
        return {"found": False, "message": "No ~/.openclaw directory found"}
    result = {"found": True, "items": []}
    src = OPENCLAW_HOME

    # SOUL.md
    soul = src / "SOUL.md"
    if soul.exists():
        result["items"].append({"type": "SOUL.md", "source": str(soul), "size": soul.stat().st_size})

    # Memories
    memories = src / "MEMORY.md"
    if memories.exists():
        result["items"].append({"type": "MEMORY.md", "source": str(memories), "size": memories.stat().st_size})
    user_md = src / "USER.md"
    if user_md.exists():
        result["items"].append({"type": "USER.md", "source": str(user_md), "size": user_md.stat().st_size})

    # Skills directory
    skills_dir = src / "skills"
    if skills_dir.exists():
        skills = list(skills_dir.rglob("*.md"))
        result["items"].append({"type": "skills", "count": len(skills), "source": str(skills_dir)})

    # Config
    cfg = src / "config" / "user_config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
            keys = list(data.keys())
            result["items"].append({"type": "config", "keys": keys, "source": str(cfg)})
        except (json.JSONDecodeError, OSError):
            result["items"].append({"type": "config", "note": "found but unreadable"})

    # .env secrets
    env_file = src / "config" / ".env"
    if env_file.exists():
        result["items"].append({"type": ".env secrets", "source": str(env_file), "size": env_file.stat().st_size})

    # AGENTS.md workspace instructions
    agents = src / "AGENTS.md"
    if agents.exists():
        result["items"].append({"type": "AGENTS.md", "source": str(agents), "size": agents.stat().st_size})

    # TTS assets
    audio = src / "audio"
    if audio.exists():
        files = list(audio.iterdir())
        result["items"].append({"type": "TTS assets", "count": len(files), "source": str(audio)})

    return result


def migrate(dry_run: bool = False, preset: str | None = None, overwrite: bool = False) -> dict:
    """Migrate from ~/.openclaw to ~/.gogeta.

    Presets:
      - None (default): full migration including secrets
      - "user-data": skip secrets/env
      - "skills-only": only migrate skills

    Returns summary dict.
    """
    if not detect_openclaw():
        return {"success": False, "message": "No ~/.openclaw directory found"}

    if dry_run:
        return preview()

    result = {"success": True, "migrated": [], "skipped": []}
    src = OPENCLAW_HOME
    dst = GOGETA_HOME

    def _cp(rel: str, label: str):
        s = src / rel
        d = dst / rel
        if s.exists():
            if d.exists() and not overwrite:
                result["skipped"].append(f"{label} (exists, use --overwrite)")
                return
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(s), str(d))
            result["migrated"].append(label)

    def _cp_dir(rel: str, label: str):
        s = src / rel
        d = dst / rel
        if s.exists():
            if d.exists() and not overwrite:
                result["skipped"].append(f"{label} (exists, use --overwrite)")
                return
            d.parent.mkdir(parents=True, exist_ok=True)
            if d.exists():
                shutil.rmtree(str(d))
            shutil.copytree(str(s), str(d))
            result["migrated"].append(label)

    if preset == "skills-only":
        _cp_dir("skills", "skills/")
        return result

    # Full migration
    _cp("SOUL.md", "SOUL.md")
    _cp("MEMORY.md", "MEMORY.md")
    _cp("USER.md", "USER.md")
    _cp_dir("skills", "skills/")

    # Config merge
    src_cfg = src / "config" / "user_config.json"
    dst_cfg = dst / "config" / "user_config.json"
    if src_cfg.exists():
        try:
            src_data = json.loads(src_cfg.read_text())
            if dst_cfg.exists():
                dst_data = json.loads(dst_cfg.read_text())
            else:
                dst_data = {}
            dst_data.setdefault("identity", {}).setdefault("gogeta_name", src_data.get("gogeta_name", "GOGETA"))
            dst_data.setdefault("identity", {}).setdefault("user_name", src_data.get("user_name", ""))
            dst_data.setdefault("identity", {}).setdefault("address_as", src_data.get("address_as", "sir"))
            inf = src_data.get("inference", {})
            if inf.get("provider"):
                dst_data.setdefault("inference", {})["provider"] = inf["provider"]
            if inf.get("model"):
                dst_data.setdefault("inference", {})["model"] = inf["model"]
            if inf.get("api_key"):
                dst_data.setdefault("inference", {})["api_key"] = inf["api_key"]
            msgs = src_data.get("messaging", [])
            if msgs:
                dst_data["messaging"] = msgs
            dst_cfg.parent.mkdir(parents=True, exist_ok=True)
            dst_cfg.write_text(json.dumps(dst_data, indent=2))
            result["migrated"].append("config (merged)")
        except (json.JSONDecodeError, OSError) as e:
            result["skipped"].append(f"config (error: {e})")

    if preset != "user-data":
        # .env secrets
        src_env = src / "config" / ".env"
        dst_env = dst / "config" / ".env"
        if src_env.exists():
            if dst_env.exists() and not overwrite:
                # Append missing keys
                existing = dst_env.read_text()
                new_lines = []
                for line in src_env.read_text().splitlines():
                    if "=" in line:
                        key = line.split("=", 1)[0]
                        if key not in existing:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                if new_lines:
                    dst_env.write_text(existing + "\n" + "\n".join(new_lines))
                    result["migrated"].append(".env (appended)")
                else:
                    result["skipped"].append(".env (no new keys)")
            else:
                dst_env.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_env), str(dst_env))
                result["migrated"].append(".env")

        # AGENTS.md
        _cp("AGENTS.md", "AGENTS.md")

        # TTS audio assets
        _cp_dir("audio", "audio/")

        # Command allowlist
        _cp("config/allowlist.json", "allowlist.json")

        # Workspace instructions
        _cp("AGENTS.md", "AGENTS.md")

    return result
