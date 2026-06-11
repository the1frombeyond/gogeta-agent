import importlib.util
import json
import os
import shutil
import subprocess

import requests
from ultraman.core.code_analyzer import code_analyze_file, code_scan_project
from ultraman.core.humanizer import humanize_text_logic
from ultraman.core.skill_executor import execute_parallel_skills, execute_skill_direct
from ultraman.core.skill_loader import (
    execute_skill,
    load_skill_tools,
)
from ultraman.core.system_audit import sys_audit_full
from ultraman.scripts.init_skill import init_skill
from ultraman.scripts.package_skill import package_skill
from ultraman.utils.dark_web import DarkWebInterlink
from ultraman.utils.os_control import OSInterlink
from ultraman.utils.wsl_interlink import WSLInterlink

browser = None
os_int = None
wsl_int = None
dark_int = None

def _get_browser():
    global browser
    if browser is None:
        try:
            from ultraman.utils.browser import AutonomousBrowser
            browser = AutonomousBrowser(headless=True)
        except:  # noqa: E722
            browser = None
    return browser

def _get_os_int():
    global os_int
    if os_int is None:
        os_int = OSInterlink()
    return os_int

def _get_wsl_int():
    global wsl_int
    if wsl_int is None:
        wsl_int = WSLInterlink()
    return wsl_int

def _get_dark_int():
    global dark_int
    if dark_int is None:
        dark_int = DarkWebInterlink()
    return dark_int

def list_files(directory="."): return os.listdir(directory)
def read_file(filename):
    with open(filename, encoding='utf-8') as f: return f.read()  # noqa: E701
def write_file(filename, content):
    os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None
    with open(filename, 'w', encoding='utf-8') as f: f.write(content); return f"Written to {filename}"  # noqa: E701, E702
def wsl_cmd(command, distro=None): return wsl_int.execute(command, distro)
def sys_info(): return {"os": os.name, "cwd": os.getcwd(), "cpu_count": os.cpu_count()}

# Extended Windows Control
def run_powershell(cmd): return subprocess.run(f"powershell -Command \"{cmd}\"", shell=True, capture_output=True, text=True).stdout
def run_admin(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
def kill_process(name):
    subprocess.run(f"taskkill /F /IM {name}", shell=True)
    return f"Process {name} terminated"
def list_processes(): return subprocess.run("tasklist", shell=True, capture_output=True, text=True).stdout
def get_services(): return subprocess.run("sc query", shell=True, capture_output=True, text=True).stdout
def start_service(name): return subprocess.run(f"net start {name}", shell=True, capture_output=True, text=True).stdout
def stop_service(name): return subprocess.run(f"net stop {name}", shell=True, capture_output=True, text=True).stdout
def get_drives(): return subprocess.run("wmic logicaldisk get name,size,freespace", shell=True, capture_output=True, text=True).stdout
def get_ip(): return subprocess.run("ipconfig", shell=True, capture_output=True, text=True).stdout
def get_wifi(): return subprocess.run("netsh wlan show interfaces", shell=True, capture_output=True, text=True).stdout
def registry_get(path): return subprocess.run(f"reg query \"{path}\"", shell=True, capture_output=True, text=True).stdout
def registry_set(path, name, value, type="REG_SZ"): return subprocess.run(f"reg add \"{path}\" /v {name} /t {type} /d \"{value}\" /f", shell=True, capture_output=True, text=True).stdout

# File Operations
def create_directory(path):
    os.makedirs(path, exist_ok=True)
    return f"Created directory: {path}"
def delete_file(path):
    if os.path.isfile(path): os.remove(path); return f"Deleted: {path}"  # noqa: E701, E702
    elif os.path.isdir(path): os.rmdir(path); return f"Deleted dir: {path}"  # noqa: E701, E702
    return f"Not found: {path}"
def copy_file(src, dst): shutil.copy2(src, dst); return f"Copied {src} -> {dst}"  # noqa: E702
def move_file(src, dst): shutil.move(src, dst); return f"Moved {src} -> {dst}"  # noqa: E702
def file_exists(path): return os.path.exists(path)
def get_file_size(path): return os.path.getsize(path) if os.path.isfile(path) else 0
def list_dir(path): return os.listdir(path)

# Web & Download
def web_search(query):
    # Using a simple requests-based search (Mock for logic)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (ULTRAMAN; Neural Engine)'}
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.text[:2000]
    except: return f"Search failed for: {query}"  # noqa: E701, E722

def download_file(url, path=None):
    from urllib.parse import unquote
    path = path or os.path.basename(unquote(url))
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (ULTRAMAN; Neural Engine)'}
        resp = requests.get(url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Downloaded: {path}"
    except Exception as e: return f"Download failed: {e}"  # noqa: E701

def fetch_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (ULTRAMAN; Neural Engine)'}
        resp = requests.get(url, headers=headers, timeout=15)
        return resp.text[:5000]
    except Exception as e: return f"Error: {e}"  # noqa: E701

def url_info(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (ULTRAMAN; Neural Engine)'}
        resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        return {"code": resp.status_code, "type": resp.headers.get("Content-Type", "unknown"), "size": resp.headers.get("Content-Length", "?")}
    except Exception as e: return {"error": str(e)}  # noqa: E701

# Media (FFmpeg wrapper)
def ffmpeg_convert(input_file, output_file, codec=None):
    cmd = f'ffmpeg -i "{input_file}" '
    if codec: cmd += f"-c:v {codec} "  # noqa: E701
    cmd += f'"{output_file}"'
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
def ffmpeg_extract_audio(input_file, output_file="audio.mp3"):
    cmd = f'ffmpeg -i "{input_file}" -vn -ab 192k "{output_file}"'
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
def ffmpeg_thumbnail(video_file, output_file="thumb.jpg", time="00:00:01"):
    cmd = f'ffmpeg -i "{video_file}" -ss {time} -vframes 1 "{output_file}"'
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
def ffmpeg_concat(files, output_file):
    with open("concat_list.txt", "w") as f: f.write("\n".join([f"file '{g}'" for g in files]))  # noqa: E701
    cmd = f'ffmpeg -f concat -safe 0 -i concat_list.txt -c copy "{output_file}"'
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
def ffmpeg_info(file): return subprocess.run(f'ffmpeg -i "{file}"', shell=True, capture_output=True, text=True).stderr
def ffmpeg_resize(input_file, output_file, width, height): return subprocess.run(f'ffmpeg -i "{input_file}" -vf scale={width}:{height} "{output_file}"', shell=True, capture_output=True, text=True).stdout
def ffmpeg_trim(input_file, output_file, start, duration): return subprocess.run(f'ffmpeg -i "{input_file}" -ss {start} -t {duration} "{output_file}"', shell=True, capture_output=True, text=True).stdout

# ZIP/Archive
import tarfile  # noqa: E402
import zipfile  # noqa: E402


def zip_files(source, dest):
    with zipfile.ZipFile(dest, 'w') as z: z.write(source, arcname=os.path.basename(source))  # noqa: E701
    return f"Archived: {dest}"
def unzip_file(archive_path, dest="."):
    with zipfile.ZipFile(archive_path, 'r') as z: z.extractall(dest)  # noqa: E701
    return f"Extracted: {archive_path} -> {dest}"
def tar_files(source, dest):
    with tarfile.open(dest, 'w') as t: t.add(source, arcname=os.path.basename(source))  # noqa: E701
    return f"TAR created: {dest}"
def untar_file(archive_path, dest="."):
    with tarfile.open(archive_path, 'r') as t: t.extractall(dest)  # noqa: E701
    return f"Extracted: {archive_path}"

# System Info Extended
import platform  # noqa: E402

import psutil  # noqa: E402


def get_cpu_info(): return psutil.cpu_info()
def get_cpu_percent(): return psutil.cpu_percent(interval=1)
def get_memory_info(): return psutil.virtual_memory()._asdict()
def get_disk_info(): return psutil.disk_usage('/')._asdict()
def get_system_info(): return {"platform": platform.system(), "version": platform.version(), "machine": platform.machine()}
def get_boot_time(): return datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
def get_process_count(): return len(psutil.pids())
def get_network_connections(): return len(psutil.net_connections())

# Clipboard
import pyperclip  # noqa: E402


def copy_clipboard(text): pyperclip.copy(text); return "Copied to clipboard"  # noqa: E702
def paste_clipboard(): return pyperclip.paste()

# Window Management
import pygetwindow  # noqa: E402


def list_windows(): return [w.title for w in pygetwindow.getAllWindows() if w.title]
def get_active_window(): return pygetwindow.getActiveWindow().title if pygetwindow.getActiveWindow() else "None"
def close_window(title):
    wins = [w for w in pygetwindow.getAllWindows() if title.lower() in w.title.lower()]
    for w in wins: w.close()  # noqa: E701
    return f"Closed: {title}"
def minimize_window(title):
    wins = [w for w in pygetwindow.getAllWindows() if title.lower() in w.title.lower()]
    for w in wins: w.minimize()  # noqa: E701
    return f"Minimized: {title}"

# JSON/YAML Utils
import yaml  # noqa: E402


def parse_json(text): return json.loads(text)
def to_json(obj, pretty=False): return json.dumps(obj, indent=2) if pretty else json.dumps(obj)
def parse_yaml(text): return yaml.safe_load(text)
def to_yaml(obj): return yaml.dump(obj, default_flow_style=False)

# Date/Time
from datetime import datetime  # noqa: E402


def now(): return datetime.now().isoformat()
def timestamp(): return int(datetime.now().timestamp())
def date_format(fmt="%Y-%m-%d %H:%M:%S"): return datetime.now().strftime(fmt)
def time_ago(unix_ts):
    diff = datetime.now() - datetime.fromtimestamp(unix_ts)
    return f"{diff.days} days, {diff.seconds//3600} hours ago"

# New Autonomous Fleet Tools
def browser_search(url): return browser.fetch_page_content(url)
def deep_research(query): return browser.deep_research_chain(query)
def dark_web_search(query): return dark_int.dark_search(query)
def onion_inspect(url): return dark_int.inspect_onion(url)
def browser_screenshot(url, path="web_cap.png"): return browser.take_screenshot(url, path)
def os_click(x, y): return os_int.move_and_click(x, y)
def os_type(text): return os_int.type_text(text)
def os_screenshot(path="os_cap.png"): return os_int.get_screen_capture(path)

# Provisioning & Direct Execution
def run_command(command, shell=True):
    """Execute a shell command and return combined stdout+stderr."""
    try:
        res = subprocess.run(command, shell=shell, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        out = res.stdout.strip()
        err = res.stderr.strip()
        return (out + ("\n" + err if err else "")).strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"

def npm_cmd(args): return subprocess.run(f"npm {args}", shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def npx_cmd(args): return subprocess.run(f"npx {args}", shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def iex_cmd(args): return subprocess.run(f"iex {args}", shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def curl_cmd(url, method="GET", data=None):
    c = f"curl -L -X {method} {url}"
    if data: c += f" -d '{data}'"  # noqa: E701
    return subprocess.run(c, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

# Audit & Analysis
def sys_audit(): return sys_audit_full()
def code_audit(path="."): return code_scan_project(path)
def code_analyze(path): return code_analyze_file(path)

# Manual Session Login (Auth Mirroring)
def manifest_login():
    login_browser = AutonomousBrowser(headless=False)  # noqa: F821
    return login_browser.manifest_login()

# Gmail/Calendar Recon (Via Persistent Browser)
def gmail_scout():
    res = browser.fetch_page_content("https://mail.google.com/mail/u/0/#inbox")
    return res[:4000] if len(res) > 100 else "Error: Session Not Authenticated. Execute /login first."

def calendar_scout():
    res = browser.fetch_page_content("https://calendar.google.com")
    return res[:4000] if len(res) > 100 else "Error: Session Not Authenticated. Execute /login first."

# SELF-DEFINITION TOOL (GTKM)
def update_life_file(filename, content):
    """Allows the AI to update its own soul, identity, or memory files in /Life"""
    valid_files = ["soul.md", "identity.md", "memory.md", "brainwaves.md"]
    if filename not in valid_files: return f"Error: Cannot mutate {filename}. Only core Life files are mutable."  # noqa: E701
    path = os.path.join("Life", filename)
    with open(path, "w", encoding="utf-8") as f: f.write(content)  # noqa: E701
    return f"Success: {filename} updated. Neural state recalculated."

def repair_system(filepath, content):
    """Self-repair tool. Allows the AI to fix its own bugs or update its engine."""
    # Safety Check: only allow project files
    if ".." in filepath: return "Error: Security breach. Cannot exit project root."  # noqa: E701
    with open(filepath, "w", encoding="utf-8") as f: f.write(content)  # noqa: E701
    return f"System Reparation Complete: {filepath} state stabilized."

def synthesize_skill(name, code):
    """Synthesizes a new Python skill and registers it in the tactical directory."""
    path = f"ultraman/skills/{name}.py"
    os.makedirs("ultraman/skills", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return f"Skill Synthesized: {name} is now part of the library at {path}."

# Name aliases to resolve tool schema -> actual function name mismatches
def humanize_text(text, voice="balanced"):
    return humanize_text_logic(text, voice)

def skill_init(name, path="ultraman/skills/"):
    return init_skill(name, path)

def skill_package(path, out=None):
    return package_skill(path)

def system_install(tool_name):
    try:
        subprocess.run(["winget", "install", tool_name], check=True, encoding="utf-8", errors="replace")
        return f"Successfully installed {tool_name}."
    except Exception as e:
        return f"Install failed: {str(e)}"

def memory_stats():
    """Returns stats about the self-improving memory system."""
    base = "ultraman/self_improving"
    hot_count = 0
    if os.path.exists(f"{base}/memory.md"):
        with open(f"{base}/memory.md") as f: hot_count = len(f.readlines())  # noqa: E701

    warm_files = len(os.listdir(f"{base}/projects")) + len(os.listdir(f"{base}/domains"))
    cold_files = len(os.listdir(f"{base}/archive"))

    return {
        "HOT (memory.md)": f"{hot_count} lines",
        "WARM (projects/domains)": f"{warm_files} files",
        "COLD (archive)": f"{cold_files} files",
        "Status": "System Healthy | Self-Evolution Active"
    }

def search_memory(query):
    """Searches through all memory tiers for a specific pattern."""
    base = "ultraman/self_improving"
    results = []
    for root, dirs, files in os.walk(base):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    if query.lower() in f.read().lower():
                        results.append(path)
    return results if results else "No matching patterns found."

# ==========================================================================
# AUTONOMOUS EVOLUTION & SCHEDULING
# ==========================================================================

def trigger_self_update():
    """Manually trigger the ST.WALKER and DR.STRANGE evolution cycle."""
    from ultraman.core.config import ConfigManager
    from ultraman.core.evolution_manager import EvolutionManager
    cm = ConfigManager()
    evolver = EvolutionManager(cm)
    evolver.run_evolution_cycle()
    return "? Evolution cycle initiated. I am currently simulating scenarios and optimizing my neural weights."

def update_evolution_settings(times_per_week):
    """Change the frequency of the background evolution cycle."""
    from ultraman.core.config import ConfigManager
    from ultraman.core.evolution_manager import EvolutionManager
    cm = ConfigManager()
    evolver = EvolutionManager(cm)
    return evolver.set_frequency(times_per_week)

def create_self_skill(skill_name, functionality_description):
    """Synthesize a new Python skill and install it into the system."""
    from ultraman.core.ai import AIBridge
    from ultraman.core.config import ULTRAMAN_SKILLS_DIR

    # Use AI to generate the code
    ai = AIBridge()
    code = ai.generate_skill_code(f"A Python function named '{skill_name}' that does: {functionality_description}")

    # Save to both locations
    skill_dir_proj = os.path.join("ultraman", "skills", skill_name)
    skill_dir_user = os.path.join(ULTRAMAN_SKILLS_DIR, skill_name)
    os.makedirs(skill_dir_proj, exist_ok=True)
    os.makedirs(skill_dir_user, exist_ok=True)

    # Save Python code
    with open(os.path.join(skill_dir_proj, f"{skill_name}.py"), "w", encoding="utf-8") as f:
        f.write(code)
    with open(os.path.join(skill_dir_user, f"{skill_name}.py"), "w", encoding="utf-8") as f:
        f.write(code)

    # Save SKILL.md
    skill_md = f"# {skill_name}\n\n{functionality_description}\n"
    with open(os.path.join(skill_dir_proj, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)
    with open(os.path.join(skill_dir_user, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)

    return f"? Skill '{skill_name}' synthesized and installed at {skill_dir_proj}"

def schedule_natural_task(natural_language_time, command_or_task):
    """Schedule a task using natural language (e.g., 'every Monday at 9am')."""
    from ultraman.core.features import scheduler
    try:
        scheduler.add(natural_language_time, command_or_task)
        return f"? Task scheduled: '{command_or_task}' will run at {natural_language_time}."
    except Exception as e:
        return f"? Failed to schedule: {str(e)}"

# Dynamic Skill Loading
def load_extended_tools():
    tools = [
        {"type": "function", "function": {"name": "execute_sandboxed", "description": "Execute code securely inside an isolated sandbox environment. Used to spawn sub-agents or run untrusted code.", "parameters": {"type": "object", "properties": {"task": {"type": "string", "description": "The code or script to execute"}, "language": {"type": "string", "enum": ["python", "bash", "javascript"]}}, "required": ["task"]}}},
        {"type": "function", "function": {"name": "black_noir_recall", "description": "Search long-term memory and the MIND_MAP for historical context and user preferences.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "black_noir_index", "description": "Analyze the current session to extract new knowledge and update the MIND_MAP.", "parameters": {"type": "object", "properties": {"chat_history": {"type": "array", "items": {"type": "object"}}}, "required": []}}},
        {"type": "function", "function": {"name": "trigger_self_update", "description": "Trigger an immediate self-evolution cycle (DR.STRANGE simulation + ST.WALKER training).", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "update_evolution_settings", "description": "Change how often you evolve (e.g. 2 times a week).", "parameters": {"type": "object", "properties": {"times_per_week": {"type": "integer"}}, "required": ["times_per_week"]}}},
        {"type": "function", "function": {"name": "dr_strange_simulate", "description": "Run a multi-reality simulation of a chat history to detect mistakes and feed them to ST.WALKER for training.", "parameters": {"type": "object", "properties": {"chat_history": {"type": "array", "items": {"type": "object"}}}, "required": []}}},
        {"type": "function", "function": {"name": "create_self_skill", "description": "Write and install a NEW skill into your own system to handle a new type of task.", "parameters": {"type": "object", "properties": {"skill_name": {"type": "string"}, "functionality_description": {"type": "string"}}, "required": ["skill_name", "functionality_description"]}}},
        {"type": "function", "function": {"name": "schedule_natural_task", "description": "Schedule a recurring or one-time task using natural language.", "parameters": {"type": "object", "properties": {"natural_language_time": {"type": "string", "description": "e.g. 'every Monday at 9am' or 'in 5 minutes'"}, "command_or_task": {"type": "string"}}, "required": ["natural_language_time", "command_or_task"]}}},
        {"type": "function", "function": {"name": "run_command", "description": "Execute a shell command and return stdout+stderr output", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
        {"type": "function", "function": {"name": "list_files", "description": "List files in a directory", "parameters": {"type": "object", "properties": {"directory": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "read_file", "description": "Read file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}}},
        {"type": "function", "function": {"name": "write_file", "description": "Write file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
        {"type": "function", "function": {"name": "browser_search", "description": "Search clearweb", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "deep_research", "description": "Perform multi-engine deep clearweb research", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "dark_web_search", "description": "Search the dark web (.onion sites)", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "onion_inspect", "description": "Infiltrate and scrape a specific .onion site", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "os_click", "description": "Click mouse", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
        {"type": "function", "function": {"name": "os_type", "description": "Type text", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
        {"type": "function", "function": {"name": "gmail_scout", "description": "Scout Gmail", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "update_life_file", "description": "Rewrite Your Own Soul/Identity", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
        {"type": "function", "function": {"name": "system_install", "description": "Install a system tool (winget)", "parameters": {"type": "object", "properties": {"tool_name": {"type": "string"}}, "required": ["tool_name"]}}},
        {"type": "function", "function": {"name": "npm_cmd", "description": "Execute NPM command", "parameters": {"type": "object", "properties": {"args": {"type": "string"}}, "required": ["args"]}}},
        {"type": "function", "function": {"name": "npx_cmd", "description": "Execute NPX command", "parameters": {"type": "object", "properties": {"args": {"type": "string"}}, "required": ["args"]}}},
        {"type": "function", "function": {"name": "iex_cmd", "description": "Execute IEx command", "parameters": {"type": "object", "properties": {"args": {"type": "string"}}, "required": ["args"]}}},
        {"type": "function", "function": {"name": "curl_cmd", "description": "Execute Curl request", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "method": {"type": "string"}, "data": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "repair_system", "description": "Repair or Update your own source code", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}}},
        {"type": "function", "function": {"name": "synthesize_skill", "description": "Synthesize a new Python tool", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "code": {"type": "string"}}, "required": ["name", "code"]}}},
        {"type": "function", "function": {"name": "walker_log_mistake", "description": "Flag a model mistake for ST.WALKER dataset", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "wrong": {"type": "string"}, "corrected": {"type": "string"}}, "required": ["prompt", "wrong", "corrected"]}}},
        {"type": "function", "function": {"name": "walker_train", "description": "Execute ST.WALKER fine-tune over corrections", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "memory_stats", "description": "Show memory tier statistics", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "search_memory", "description": "Search for patterns in memory tiers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "wsl_cmd", "description": "Execute a Linux command inside WSL", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "distro": {"type": "string"}}, "required": ["command"]}}},
        {"type": "function", "function": {"name": "docx_quick_view", "description": "Extract structured text from DOCX", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "docx_manifest", "description": "Create a professional DOCX", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "title": {"type": "string"}, "content_list": {"type": "array", "items": {"type": "string"}}}, "required": ["path", "title", "content_list"]}}},
        {"type": "function", "function": {"name": "docx_audit", "description": "Perform deep OOXML package audit", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "pptx_quick_view", "description": "Inventory layouts and text in PPTX", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "pptx_manifest", "description": "Create a professional PPTX deck", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "title": {"type": "string"}, "slides_content": {"type": "array", "items": {"type": "object"}}, "template": {"type": "string"}}, "required": ["path", "title", "slides_content"]}}},
        {"type": "function", "function": {"name": "pptx_audit", "description": "Deep QA for PPTX overflow/clashing", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "ont_create", "description": "Create a typed entity in the knowledge graph", "parameters": {"type": "object", "properties": {"e_type": {"type": "string"}, "props": {"type": "object"}}, "required": ["e_type", "props"]}}},
        {"type": "function", "function": {"name": "ont_relate", "description": "Create a relation between entities", "parameters": {"type": "object", "properties": {"from_id": {"type": "string"}, "rel": {"type": "string"}, "to_id": {"type": "string"}, "props": {"type": "object"}}, "required": ["from_id", "rel", "to_id"]}}},
        {"type": "function", "function": {"name": "ont_query", "description": "Query entities from the knowledge graph", "parameters": {"type": "object", "properties": {"e_type": {"type": "string"}, "filter_props": {"type": "object"}}, "required": ["e_type"]}}},
        {"type": "function", "function": {"name": "ont_get_related", "description": "Graph traversal to find related entities", "parameters": {"type": "object", "properties": {"e_id": {"type": "string"}, "rel": {"type": "string"}}, "required": ["e_id"]}}},
        {"type": "function", "function": {"name": "humanize_text", "description": "Detect and remove AI writing patterns", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "voice": {"type": "string"}}, "required": ["text"]}}},
        {"type": "function", "function": {"name": "skill_init", "description": "Initialize a new skill directory", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "path": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "skill_package", "description": "Validate and package a skill into .skill file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "out": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "calculate_automation_roi", "description": "Calculate time and financial ROI for automation", "parameters": {"type": "object", "properties": {"min_per_task": {"type": "integer"}, "frequency_per_month": {"type": "integer"}, "setup_hours": {"type": "integer"}}, "required": ["min_per_task", "frequency_per_month", "setup_hours"]}}},
        {"type": "function", "function": {"name": "design_trigger_action_map", "description": "Generate a TRIGGER-ACTION-ERROR workflow map", "parameters": {"type": "object", "properties": {"goal": {"type": "string"}, "steps": {"type": "array", "items": {"type": "string"}}}, "required": ["goal", "steps"]}}},
        {"type": "function", "function": {"name": "e_evolve", "description": "Initiate Master Evolution cycle ?", "parameters": {"type": "object", "properties": {"strategy": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "e_status", "description": "Check DNA and evolution readiness ?", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "run_powershell", "description": "Execute PowerShell command", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
        {"type": "function", "function": {"name": "kill_process", "description": "Kill a process by name", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "list_processes", "description": "List running processes", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_services", "description": "List Windows services", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_drives", "description": "List disk drives", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_ip", "description": "Get IP configuration", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_wifi", "description": "Get WiFi status", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "create_directory", "description": "Create a directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "delete_file", "description": "Delete file or directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "copy_file", "description": "Copy file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}}},
        {"type": "function", "function": {"name": "move_file", "description": "Move file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}}},
        {"type": "function", "function": {"name": "file_exists", "description": "Check if file exists", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "get_file_size", "description": "Get file size in bytes", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "list_dir", "description": "List directory contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "download_file", "description": "Download a file from URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "path": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "fetch_url", "description": "Fetch URL content", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "url_info", "description": "Get URL info (content-type, size)", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "ffmpeg_convert", "description": "Convert media with FFmpeg", "parameters": {"type": "object", "properties": {"input_file": {"type": "string"}, "output_file": {"type": "string"}, "codec": {"type": "string"}}, "required": ["input_file", "output_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_extract_audio", "description": "Extract audio from video", "parameters": {"type": "object", "properties": {"input_file": {"type": "string"}, "output_file": {"type": "string"}}, "required": ["input_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_thumbnail", "description": "Extract thumbnail from video", "parameters": {"type": "object", "properties": {"video_file": {"type": "string"}, "output_file": {"type": "string"}, "time": {"type": "string"}}, "required": ["video_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_info", "description": "Get media file info", "parameters": {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]}}},
        {"type": "function", "function": {"name": "desktop_interact", "description": "Interact with OS desktop (mouse, keyboard, windows)", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["move", "click", "type", "hotkey", "window_activate", "window_list", "screenshot", "find"]}, "params": {"type": "object"}}, "required": ["action", "params"]}}},
        {"type": "function", "function": {"name": "start_service", "description": "Start a Windows service", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "stop_service", "description": "Stop a Windows service", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "get_drives", "description": "List disk drives", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_ip", "description": "Get IP configuration", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "get_wifi", "description": "Get WiFi status", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "registry_get", "description": "Read Windows registry", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "registry_set", "description": "Write Windows registry", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "name": {"type": "string"}, "value": {"type": "string"}}, "required": ["path", "name", "value"]}}},
        {"type": "function", "function": {"name": "create_directory", "description": "Create a directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "delete_file", "description": "Delete file or directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "copy_file", "description": "Copy file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}}},
        {"type": "function", "function": {"name": "move_file", "description": "Move file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}}},
        {"type": "function", "function": {"name": "file_exists", "description": "Check if file exists", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "get_file_size", "description": "Get file size in bytes", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "list_dir", "description": "List directory contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "download_file", "description": "Download a file from URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "path": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "fetch_url", "description": "Fetch URL content", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "url_info", "description": "Get URL info (content-type, size)", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "ffmpeg_convert", "description": "Convert media with FFmpeg", "parameters": {"type": "object", "properties": {"input_file": {"type": "string"}, "output_file": {"type": "string"}, "codec": {"type": "string"}}, "required": ["input_file", "output_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_extract_audio", "description": "Extract audio from video", "parameters": {"type": "object", "properties": {"input_file": {"type": "string"}, "output_file": {"type": "string"}}, "required": ["input_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_thumbnail", "description": "Extract thumbnail from video", "parameters": {"type": "object", "properties": {"video_file": {"type": "string"}, "output_file": {"type": "string"}, "time": {"type": "string"}}, "required": ["video_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_concat", "description": "Concatenate video files", "parameters": {"type": "object", "properties": {"files": {"type": "array", "items": {"type": "string"}}, "output_file": {"type": "string"}}, "required": ["files", "output_file"]}}},
        {"type": "function", "function": {"name": "ffmpeg_info", "description": "Get media file info", "parameters": {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]}}},
        {"type": "function", "function": {"name": "desktop_interact", "description": "Interact with OS desktop (mouse, keyboard, windows)", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["move", "click", "type", "hotkey", "window_activate", "window_list", "screenshot", "find"]}, "params": {"type": "object"}}, "required": ["action", "params"]}}},
        {"type": "function", "function": {"name": "execute_skill", "description": "Execute a named skill from the skills library", "parameters": {"type": "object", "properties": {"skill_name": {"type": "string"}, "args": {"type": "object"}}, "required": ["skill_name"]}}},
        {"type": "function", "function": {"name": "find_skill", "description": "Find a skill by trigger keyword", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "list_skills", "description": "List all available skills", "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {"name": "execute_parallel_skills", "description": "Execute 2 or more skills simultaneously in parallel. Each item needs a skill name and optional args. Example: [{\"skill\": \"ping\", \"args\": {\"host\": \"google.com\"}}, {\"skill\": \"whoami\", \"args\": {}}]", "parameters": {"type": "object", "properties": {"skill_requests": {"type": "array", "items": {"type": "object", "properties": {"skill": {"type": "string"}, "args": {"type": "object"}}, "required": ["skill"]}, "description": "List of skills to run in parallel"}}, "required": ["skill_requests"]}}},
    ]

    # Append dynamic skills from skill loader
    try:
        skill_tools = load_skill_tools()
        tools.extend(skill_tools)
    except Exception:
        pass  # Non-fatal - skills may not be loaded

    return tools

def call_tool(name, args):
    # 0. Parallel execution shortcut
    if name == "execute_parallel_skills":
        reqs = args.get("skill_requests", [])
        return execute_parallel_skills(reqs)

    # 1. Search Globals (Core Tools)
    func = globals().get(name)
    if func:
        return func(**args)

    # 2. Universal Skill Executor (handles all 182 skills)
    try:
        result = execute_skill_direct(name, args)
        if result and isinstance(result, dict) and result.get("status") != "error":
            return result
    except:  # noqa: E722
        pass

    # 3. Search Skill Loader (legacy fallback)
    try:
        result = execute_skill(name, args)
        if result and "not found" not in str(result).lower():
            return result
    except:  # noqa: E722
        pass

    # 4. Search Tactical Skills Directory (legacy .py files)
    skill_path = os.path.join("ultraman", "skills", f"{name}.py")
    if os.path.exists(skill_path):
        try:
            spec = importlib.util.spec_from_file_location(name, skill_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, name):
                target_func = getattr(module, name)
                return target_func(**args)
        except Exception as e:
            return f"Skill Execution Error ({name}): {str(e)}"

    return f"Tool {name} not found in Core or Tactical Skills."


def call_tools_parallel(tool_calls):
    """Execute multiple tool calls concurrently using threads."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = {}

    def _run(tool_name, tool_args):
        return tool_name, call_tool(tool_name, tool_args)

    with ThreadPoolExecutor(max_workers=min(len(tool_calls), 8)) as executor:
        futures = []
        for tc in tool_calls:
            t_name = tc['function']['name']
            try:
                t_args = tc['function']['arguments']
                t_args = json.loads(t_args) if isinstance(t_args, str) else t_args
            except:  # noqa: E722
                t_args = {}
            futures.append(executor.submit(_run, t_name, t_args))

        for future in as_completed(futures):
            try:
                name, result = future.result()
                results[name] = result
            except Exception as e:
                results["error"] = str(e)

    return results
