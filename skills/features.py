"""
ULTRAMAN Extended Features
- Voice Input
- Auto-Save
- Plugin System
- Custom Prompts
- Command Aliases
- Web API Server
- Notifications
- Scheduled Tasks
"""

import json
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import schedule

FEATURES_CONFIG = {
    "voice_enabled": False,
    "auto_save_interval": 60,
    "plugins_dir": "plugins",
    "custom_prompts": {},
    "aliases": {},
    "web_api_port": 8080,
    "notifications_enabled": True,
}

CONFIG_FILE = ".ultraman/features.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return {**FEATURES_CONFIG, **json.load(f)}
    return FEATURES_CONFIG.copy()

def save_config(cfg):
    os.makedirs(".ultraman", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ============================================================================
# VOICE INPUT (using speech_recognition)
# ============================================================================
def voice_listen(timeout=5):
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=timeout)
        return r.recognize_google(audio)
    except Exception as e:
        return f"Voice error: {e}"

# ============================================================================
# AUTO-SAVE
# ============================================================================
class AutoSaver:
    def __init__(self, interval=60):
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self, data_provider):
        self.running = True
        self.data_provider = data_provider
        self.thread = threading.Thread(target=self._save_loop, daemon=True)
        self.thread.start()

    def _save_loop(self):
        while self.running:
            time.sleep(self.interval)
            self.save()

    def save(self):
        try:
            data = self.data_provider()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f".ultraman/sessions/autosave_{ts}.json"
            os.makedirs(".ultraman/sessions", exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except:  # noqa: E722
            pass

    def stop(self):
        self.running = False

auto_saver = AutoSaver()

# ============================================================================
# PLUGIN SYSTEM
# ============================================================================
class PluginManager:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.plugins = {}

    def load_all(self):
        if not os.path.exists(self.plugins_dir):
            return
        for f in os.listdir(self.plugins_dir):
            if f.endswith(".py"):
                self.load_plugin(f[:-3])

    def load_plugin(self, name):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, f"{self.plugins_dir}/{name}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.plugins[name] = module
            return f"Loaded: {name}"
        except Exception as e:
            return f"Error: {e}"

    def run_plugin(self, name, *args):
        if name in self.plugins:
            try:
                return self.plugins[name].run(*args)
            except:  # noqa: E722
                pass
        return "Plugin not found"

plugin_manager = PluginManager()

# ============================================================================
# CUSTOM PROMPTS
# ============================================================================
CUSTOM_PROMPTS_FILE = ".ultraman/custom_prompts.json"

def save_custom_prompt(name, prompt):
    prompts = {}
    if os.path.exists(CUSTOM_PROMPTS_FILE):
        with open(CUSTOM_PROMPTS_FILE) as f:
            prompts = json.load(f)
    prompts[name] = prompt
    with open(CUSTOM_PROMPTS_FILE, "w") as f:
        json.dump(prompts, f, indent=2)

def get_custom_prompt(name):
    if os.path.exists(CUSTOM_PROMPTS_FILE):
        with open(CUSTOM_PROMPTS_FILE) as f:
            prompts = json.load(f)
            return prompts.get(name)
    return None

# ============================================================================
# COMMAND ALIASES
# ============================================================================
ALIASES_FILE = ".ultraman/aliases.json"

def load_aliases():
    if os.path.exists(ALIASES_FILE):
        with open(ALIASES_FILE) as f:
            return json.load(f)
    return {"/m": "/multi", "/h": "/help", "/s": "/stats"}

def resolve_alias(cmd):
    aliases = load_aliases()
    for alias, full in aliases.items():
        if cmd.startswith(alias):
            return cmd.replace(alias, full, 1)
    return cmd

# ============================================================================
# WEB API SERVER
# ============================================================================
class ULTRAMAN_API_Handler(BaseHTTPRequestHandler):  # noqa: N801
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "running", "time": datetime.now().isoformat()}).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"received": len(body)}).encode())

def start_web_api(port=8080):
    server = HTTPServer(("0.0.0.0", port), ULTRAMAN_API_Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"Web API: http://localhost:{port}"

# ============================================================================
# NOTIFICATIONS
# ============================================================================
def send_notification(title, message):
    try:
        from win10toast import ToastNotifier
        t = ToastNotifier()
        t.show_toast(title, message, duration=3)
    except:  # noqa: E722
        try:
            import subprocess
            subprocess.run(['powershell', '-Command',
                f'New-BurntToast -Title "{title}" -Text "{message}"'],
                capture_output=True)
        except:  # noqa: E722
            pass

# ============================================================================
# SCHEDULED TASKS
# ============================================================================
class TaskScheduler:
    def __init__(self):
        self.jobs = []
        self.running = False
        self.thread = None

    def add(self, time_str, command, name=""):
        schedule.every().day.at(time_str).do(lambda: self.run_cmd(command))
        if not self.running:
            self.start()

    def run_cmd(self, cmd):
        import subprocess
        subprocess.run(cmd, shell=True, capture_output=True)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)

scheduler = TaskScheduler()

# ============================================================================
# PLUGIN MARKETPLACE (download from URL)
# ============================================================================
def install_plugin(url, name=None):
    import urllib.request
    try:
        content = urllib.request.urlopen(url, timeout=10).read().decode()
        name = name or url.split("/")[-1].replace(".py", "")
        path = f"plugins/{name}.py"
        with open(path, "w") as f:
            f.write(content)
        return f"Installed: {name}"
    except Exception as e:
        return f"Error: {e}"

# ============================================================================
# MOBILE COMPANION (simple HTTP server)
# ============================================================================
class MobileCompanionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
            <style>body{font-family:sans-serif;padding:20px;background:#1a1a1a;color:#e8dcc8}
            button{padding:15px 30px;font-size:16px;margin:5px;background:#d4a017;border:none;color:#1a1a1a}
            </style></head><body>
            <h1>ULTRAMAN</h1>
            <button onclick="fetch('/cmd?c=help')">Help</button>
            <button onclick="fetch('/cmd?c=stats')">Stats</button>
            <button onclick="fetch('/cmd?c=exit')">Exit</button>
            </body></html>""")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_paths = []
            self.wfile.write(b"OK")

    def do_POST(self):
        self.do_GET()

def start_mobile_companion(port=5000):
    server = HTTPServer(("0.0.0.0", port), MobileCompanionHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"Mobile: http://localhost:{port}"

# Feature enable/load
def init_features():
    cfg = load_config()
    plugin_manager.plugins_dir = cfg.get("plugins_dir", "plugins")
    return cfg

init_features()
