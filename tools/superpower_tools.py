"""Superpower tools: skill management, todo, and questions for gogeta."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

GOGETA_HOME = Path(os.environ.get("GOGETA_HOME", Path.home() / ".gogeta"))
SUPER_DIR = GOGETA_HOME / "superpowers"
SKILLS_DIR = GOGETA_HOME / "skills"
TOOLS_DIR = GOGETA_HOME / "tools"
MCPS_DIR = GOGETA_HOME / "mcps"
TODO_FILE = GOGETA_HOME / "config" / "todos.json"
QUESTIONS_FILE = GOGETA_HOME / "config" / "questions.json"

for d in [SUPER_DIR, SKILLS_DIR, TOOLS_DIR, MCPS_DIR, GOGETA_HOME / "config"]:
    d.mkdir(parents=True, exist_ok=True)


def _load_json(fp):
    if fp.exists() and fp.stat().st_size > 0:
        try:
            return json.loads(fp.read_text())
        except (json.JSONDecodeError, OSError):
            return [] if fp.suffix == ".json" else {}
    return [] if fp.suffix == ".json" else {}


def _save_json(fp, data):
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def superpower_search(query: str) -> dict:
    """Search skills.sh for skills matching query."""
    try:
        r = subprocess.run(
            ["npx", "skills", "find", query],
            capture_output=True, text=True, timeout=15,
            shell=sys.platform == "win32",
        )
        out = r.stdout or r.stderr or ""
        results = []
        for line in out.split("\n"):
            if "installs" in line and "/" in line:
                parts = line.strip().split()
                if parts:
                    results.append(parts[0])
        return {"success": True, "output": "\n".join(results[:20]) if results else f"No results for '{query}'"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Search timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def superpower_install(pkg: str) -> dict:
    """Install a skill from skills.sh. pkg format: owner/repo@skill"""
    try:
        r = subprocess.run(
            ["npx", "skills", "add", pkg],
            capture_output=True, text=True, timeout=30,
            shell=sys.platform == "win32",
        )
        out = (r.stdout or r.stderr or "").strip()
        return {"success": True, "output": out or f"Installed {pkg}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Install timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def superpower_list() -> dict:
    """List all installed skills and superpowers."""
    items = []
    for d in [SKILLS_DIR, SUPER_DIR]:
        if not d.exists():
            continue
        for entry in sorted(d.iterdir()):
            if entry.is_dir():
                items.append(f"[{d.name}] {entry.name}")
    if not items:
        return {"success": True, "output": "No skills installed."}
    return {"success": True, "output": "\n".join(items)}


def superpower_create(name: str, description: str = "", kind: str = "skill", content: str = "") -> dict:
    """Create a new local superpower (skill, tool, or MCP)."""
    name = name.lower().replace(" ", "_").replace("-", "_")
    if kind == "skill":
        skill_dir = SUPER_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        md = f"---\nname: {name}\ndescription: {description}\nversion: 1.0.0\n---\n\n{content or '# ' + name}"
        (skill_dir / "SKILL.md").write_text(md, encoding="utf-8")
        (skill_dir / f"{name}.py").write_text(f"# {name} superpower\n# {description}\n\n", encoding="utf-8")
        return {"success": True, "output": f"Created skill: {name} at {skill_dir}"}
    elif kind == "tool":
        fp = TOOLS_DIR / f"{name}.py"
        fp.write_text(content or f"# {name} tool\n# {description}\ndef run():\n    pass\n", encoding="utf-8")
        return {"success": True, "output": f"Created tool: {fp}"}
    elif kind == "mcp":
        mcp_cfg = GOGETA_HOME / "config" / "mcp_servers.json"
        config = _load_json(mcp_cfg) if mcp_cfg.exists() else {}
        config[name] = {"command": content or "echo", "args": [], "description": description}
        _save_json(mcp_cfg, config)
        return {"success": True, "output": f"Created MCP: {name}"}
    return {"success": False, "error": f"Unknown kind: {kind}"}


def superpower_auto(task: str) -> dict:
    """Auto-generate a superpower (skill + tool) for a hard task."""
    slug = task.lower().replace(" ", "_").replace("-", "_")[:40]
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    if not slug:
        slug = "auto_power"
    skill_dir = SUPER_DIR / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    md_content = (
        f"---\nname: {slug}\ndescription: Auto-generated for: {task}\nversion: 1.0.0\n---\n\n"
        f"## Description\nAuto-generated capability to handle: {task}\n\n"
        f"## Usage\nGogeta should use this superpower when the user asks about: {task}\n\n"
        f"## Instructions\nProvide AI-guided assistance for {task}.\n"
    )
    (skill_dir / "SKILL.md").write_text(md_content, encoding="utf-8")
    py_content = f"# {slug} - {task}\ndef handle_{slug}(context):\n    pass\n"
    (skill_dir / f"{slug}.py").write_text(py_content, encoding="utf-8")
    return {
        "success": True,
        "output": f"Auto-generated superpower '{slug}' at {skill_dir}\n"
        f"I created a new skill to help with: {task}\n"
        f"Try asking me about {task} and I'll use this skill!",
    }


def todo_add(text: str, priority: str = "medium") -> dict:
    """Add a todo item. Priority: high, medium, low."""
    todos = _load_json(TODO_FILE)
    todo = {
        "id": str(int(time.time() * 1000)),
        "text": text,
        "priority": priority,
        "done": False,
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    todos.append(todo)
    _save_json(TODO_FILE, todos)
    return {"success": True, "output": f"Added todo: {text} [{priority}]"}


def todo_list(filter_by: str = "all") -> dict:
    """List todos. filter_by: all, pending, done."""
    todos = _load_json(TODO_FILE)
    if filter_by == "pending":
        todos = [t for t in todos if not t["done"]]
    elif filter_by == "done":
        todos = [t for t in todos if t["done"]]
    if not todos:
        return {"success": True, "output": "No todos found."}
    lines = []
    for t in todos:
        status = "x" if t["done"] else " "
        lines.append(f"[{status}] {t['text']} ({t['priority']})")
    return {"success": True, "output": "\n".join(lines)}


def todo_done(todo_id: str) -> dict:
    """Mark a todo as done by its ID or text prefix."""
    todos = _load_json(TODO_FILE)
    for t in todos:
        if t["id"] == todo_id or t["text"].startswith(todo_id) or todo_id in t["text"]:
            t["done"] = True
            _save_json(TODO_FILE, todos)
            return {"success": True, "output": f"Done: {t['text']}"}
    return {"success": False, "error": f"Todo not found: {todo_id}"}


def question_save(question: str, answer: str = "") -> dict:
    """Save a question and answer for future reference."""
    questions = _load_json(QUESTIONS_FILE)
    q = {
        "id": str(int(time.time() * 1000)),
        "question": question,
        "answer": answer,
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    questions.append(q)
    _save_json(QUESTIONS_FILE, questions)
    return {"success": True, "output": f"Saved question: {question}"}


def question_list() -> dict:
    """List all saved questions."""
    questions = _load_json(QUESTIONS_FILE)
    if not questions:
        return {"success": True, "output": "No questions saved yet."}
    lines = []
    for q in questions[-20:]:
        has_ans = "x" if q.get("answer") else " "
        lines.append(f"[{has_ans}] {q['question']} ({q['created']})")
    return {"success": True, "output": "\n".join(lines)}


def register_tools(r):
    r.register("superpower_search", lambda p: superpower_search(p["query"]), permission="always_allow", category="superpowers")
    r.register("superpower_install", lambda p: superpower_install(p["package"]), permission="confirm", category="superpowers")
    r.register("superpower_list", lambda _p: superpower_list(), permission="always_allow", category="superpowers")
    r.register("superpower_create", lambda p: superpower_create(p.get("name", ""), p.get("description", ""), p.get("kind", "skill"), p.get("content", "")), permission="confirm", category="superpowers")
    r.register("superpower_auto", lambda p: superpower_auto(p["task"]), permission="confirm", category="superpowers")
    r.register("todo_add", lambda p: todo_add(p["text"], p.get("priority", "medium")), permission="confirm", category="tasks")
    r.register("todo_list", lambda p: todo_list(p.get("filter", "all")), permission="always_allow", category="tasks")
    r.register("todo_done", lambda p: todo_done(p["id"]), permission="confirm", category="tasks")
    r.register("question_save", lambda p: question_save(p["question"], p.get("answer", "")), permission="confirm", category="tasks")
    r.register("question_list", lambda _p: question_list(), permission="always_allow", category="tasks")
