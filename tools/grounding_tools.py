"""Grounding tools — 18 hallucination-prevention tools the model must use instead of guessing."""

import datetime
import json
import math
import os
import re
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web for current information. Use when unsure about facts, dates, prices, or news."""
    try:
        import requests
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Gogeta/1.0)"}
        r = requests.get(url, headers=headers, timeout=10)
        snippets = re.findall(r'class="result__snippet">(.*?)</(?:a|td)>', r.text, re.DOTALL)[:max_results]
        links = re.findall(r'class="result__url"[^>]*>([^<]+)', r.text)[:max_results]
        results = []
        for i, s in enumerate(snippets):
            link = links[i] if i < len(links) else ""
            results.append(f"{link.strip()}: {re.sub(r'<[^>]+>', '', s).strip()}")
        return {"success": True, "output": "\n\n".join(results) if results else "No results found"}
    except ImportError:
        return {"success": False, "error": "requests not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression safely. Use instead of guessing math."""
    allowed = set("0123456789+-*/.()%^eE pi sqrtabsintroundfloorceillogsinocostan")
    safe = re.sub(r'[^0-9+\-*/.()%^eEI \t]', '', expression)
    if not safe.strip():
        return {"success": False, "error": "Empty expression"}
    try:
        safe = safe.replace("^", "**")
        result = eval(safe, {"__builtins__": {}}, {
            "sqrt": math.sqrt, "abs": abs, "int": int, "round": round,
            "floor": math.floor, "ceil": math.ceil, "log": math.log,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "pi": math.pi, "e": math.e,
        })
        return {"success": True, "output": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def current_time(timezone: str = "local") -> dict:
    """Get the current date and time. Use instead of guessing what day or time it is."""
    try:
        now = datetime.datetime.now()
        if timezone and timezone != "local":
            import zoneinfo
            tz = zoneinfo.ZoneInfo(timezone)
            now = datetime.datetime.now(tz)
        return {"success": True, "output": now.strftime("%Y-%m-%d %H:%M:%S %Z")}
    except ImportError:
        return {"success": True, "output": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        return {"success": True, "output": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "note": str(e)}


def fetch_url(url: str) -> dict:
    """Fetch content from a URL. Use to verify what's actually at a link instead of guessing."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        import requests
        r = requests.get(url, timeout=15, headers={"User-Agent": "Gogeta/1.0"})
        text = r.text[:5000]
        return {"success": True, "output": f"Status {r.status_code}\n\n{text[:4000]}"}
    except ImportError:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Gogeta/1.0"}), timeout=15)
            text = r.read().decode("utf-8", errors="replace")[:5000]
            return {"success": True, "output": text[:4000]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_package_version(package_name: str) -> dict:
    """Check if a Python package is installed and what version. Use instead of guessing version."""
    try:
        import importlib.metadata
        ver = importlib.metadata.version(package_name)
        return {"success": True, "output": f"{package_name}=={ver}"}
    except importlib.metadata.PackageNotFoundError:
        return {"success": False, "error": f"Package '{package_name}' not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_command_exists(command: str) -> dict:
    """Check if a CLI command/tool is available on the system."""
    try:
        r = subprocess.run(["where", command] if os.name == "nt" else ["which", command],
                          capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            path = r.stdout.strip().split("\n")[0]
            return {"success": True, "output": f"Found: {path}"}
        return {"success": False, "error": f"Command '{command}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def validate_python_syntax(code: str) -> dict:
    """Validate Python code syntax without executing it. Use instead of guessing if code is correct."""
    try:
        import ast
        ast.parse(code)
        lines = code.count("\n") + 1
        return {"success": True, "output": f"Valid Python ({lines} lines)"}
    except SyntaxError as e:
        return {"success": False, "error": f"SyntaxError: {e}"}


def resolve_path(path: str) -> dict:
    """Resolve a file path — expand ~, vars, check existence. Use instead of guessing if a path exists."""
    try:
        expanded = os.path.expanduser(os.path.expandvars(path))
        p = Path(expanded).resolve()
        exists = p.exists()
        kind = "directory" if p.is_dir() else "file" if p.is_file() else "symlink" if p.is_symlink() else "unknown"
        return {"success": True, "output": f"{p}{' (exists, ' + kind + ')' if exists else ' (does not exist)'}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def dns_lookup(hostname: str) -> dict:
    """Look up DNS records for a hostname. Use instead of guessing IPs or domains."""
    try:
        ip = socket.gethostbyname(hostname)
        return {"success": True, "output": f"{hostname} → {ip}"}
    except socket.gaierror:
        return {"success": False, "error": f"Cannot resolve {hostname}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def unit_convert(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert between units (length, mass, temperature, volume, speed)."""
    conversions = {
        # Length
        ("km", "m"): 1000, ("m", "km"): 0.001, ("m", "cm"): 100, ("cm", "m"): 0.01,
        ("m", "mm"): 1000, ("mm", "m"): 0.001, ("km", "mi"): 0.621371, ("mi", "km"): 1.60934,
        ("m", "ft"): 3.28084, ("ft", "m"): 0.3048, ("cm", "in"): 0.393701, ("in", "cm"): 2.54,
        # Mass
        ("kg", "g"): 1000, ("g", "kg"): 0.001, ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
        ("g", "oz"): 0.035274, ("oz", "g"): 28.3495,
        # Temperature
        ("c", "f"): "c2f", ("f", "c"): "f2c", ("c", "k"): "c2k", ("k", "c"): "k2c",
        # Volume
        ("l", "ml"): 1000, ("ml", "l"): 0.001, ("l", "gal"): 0.264172, ("gal", "l"): 3.78541,
        # Speed
        ("kmh", "mph"): 0.621371, ("mph", "kmh"): 1.60934, ("ms", "kmh"): 3.6, ("kmh", "ms"): 0.277778,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        factor = conversions[key]
        if factor == "c2f":
            return {"success": True, "output": f"{value * 9/5 + 32:.4f} °F"}
        if factor == "f2c":
            return {"success": True, "output": f"{(value - 32) * 5/9:.4f} °C"}
        if factor == "c2k":
            return {"success": True, "output": f"{value + 273.15:.4f} K"}
        if factor == "k2c":
            return {"success": True, "output": f"{value - 273.15:.4f} °C"}
        return {"success": True, "output": f"{value * factor:.6f} {to_unit}"}
    return {"success": False, "error": f"Unknown conversion: {from_unit} → {to_unit}"}


def test_regex(pattern: str, test_string: str) -> dict:
    """Test a regex pattern against a string and show matches. Use instead of guessing regex behavior."""
    try:
        matches = re.findall(pattern, test_string)
        if matches:
            count = len(matches)
            return {"success": True, "output": f"{count} match(es): {json.dumps(matches[:20])}"}
        return {"success": True, "output": "No matches"}
    except re.error as e:
        return {"success": False, "error": f"Regex error: {e}"}


def system_info(key: str = "all") -> dict:
    """Get system information. Use instead of guessing OS, arch, Python version, etc."""
    import platform
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "hostname": platform.node(),
        "cwd": os.getcwd(),
        "home": str(Path.home()),
        "encoding": f"{sys.getfilesystemencoding() or 'utf-8'}",
    }
    if key != "all":
        return {"success": True, "output": str(info.get(key, f"Unknown key: {key}"))}
    return {"success": True, "output": json.dumps(info, indent=2)}


def check_file_hash(filepath: str, algorithm: str = "sha256") -> dict:
    """Compute a file hash. Use to verify file integrity instead of guessing."""
    import hashlib
    try:
        p = Path(filepath)
        if not p.exists():
            return {"success": False, "error": f"File not found: {filepath}"}
        if not p.is_file():
            return {"success": False, "error": f"Not a file: {filepath}"}
        h = hashlib.new(algorithm)
        h.update(p.read_bytes())
        return {"success": True, "output": f"{algorithm}: {h.hexdigest()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def what_is(term: str) -> dict:
    """Look up the definition of a term using a dictionary API. Use instead of defining terms from memory."""
    try:
        import requests
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(term)}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            meanings = data[0].get("meanings", [])
            defs = []
            for m in meanings[:3]:
                for d in m.get("definitions", [])[:2]:
                    defs.append(f"({m['partOfSpeech']}) {d.get('definition', '')}")
            return {"success": True, "output": "\n".join(defs) if defs else f"No definitions found for '{term}'"}
        return {"success": False, "error": f"'{term}' not found in dictionary"}
    except ImportError:
        return {"success": False, "error": "requests not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_port(host: str, port: int) -> dict:
    """Check if a port is open on a host. Use instead of guessing if a service is running."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((host, port))
        s.close()
        if result == 0:
            return {"success": True, "output": f"Port {port} on {host} is OPEN"}
        return {"success": True, "output": f"Port {port} on {host} is CLOSED"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_env_var(name: str) -> dict:
    """Check if an environment variable exists and return its value (or note it's unset)."""
    val = os.environ.get(name)
    if val is not None:
        return {"success": True, "output": f"${name} = {val}"}
    return {"success": True, "output": f"${name} is not set"}


def json_validate(text: str) -> dict:
    """Try to parse a string as JSON. Return the parsed value or a syntax error."""
    try:
        parsed = json.loads(text)
        return {"success": True, "output": json.dumps(parsed, indent=2)}
    except json.JSONDecodeError as e:
        return {"success": True, "output": f"Invalid JSON: {e}"}


def url_encode_decode(text: str, mode: str = "encode") -> dict:
    """URL-encode or URL-decode a string."""
    if mode == "encode":
        return {"success": True, "output": urllib.parse.quote(text, safe="")}
    elif mode == "decode":
        return {"success": True, "output": urllib.parse.unquote(text)}
    return {"success": False, "error": "mode must be 'encode' or 'decode'"}


# ── File operations ──────────────────────────────────────────────

def copy_file(source: str, dest: str) -> dict:
    """Copy a file from source to destination."""
    import shutil
    try:
        shutil.copy2(source, dest)
        return {"success": True, "output": f"Copied {source} → {dest}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def move_file(source: str, dest: str) -> dict:
    """Move or rename a file."""
    import shutil
    try:
        shutil.move(source, dest)
        return {"success": True, "output": f"Moved {source} → {dest}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_file(filepath: str) -> dict:
    """Delete a file (not directories)."""
    try:
        p = Path(filepath)
        if not p.exists():
            return {"success": False, "error": "File not found"}
        p.unlink()
        return {"success": True, "output": f"Deleted {filepath}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_dir(path: str = ".", depth: int = 1) -> dict:
    """List directory contents with details (size, modified)."""
    try:
        p = Path(path)
        if not p.is_dir():
            return {"success": False, "error": "Not a directory"}
        lines = []
        for entry in sorted(p.iterdir()):
            if entry.is_file():
                size = entry.stat().st_size
                mod = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime("%H:%M")
                lines.append(f"{'📄 ' if size < 1024 else '📦 '}{entry.name:<30} {_fmt_size(size):>8}  {mod}")
            elif entry.is_dir():
                lines.append(f"📁 {entry.name}/")
        return {"success": True, "output": "\n".join(lines) or "(empty directory)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


def find_files(pattern: str, path: str = ".") -> dict:
    """Find files matching a glob pattern."""
    try:
        import glob as glob_mod
        matches = sorted(glob_mod.glob(pattern, root_dir=path, recursive=True))
        return {"success": True, "output": "\n".join(matches) if matches else "No matches"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_info(filepath: str) -> dict:
    """Get file metadata: size, modified time, permissions."""
    try:
        p = Path(filepath)
        if not p.exists():
            return {"success": False, "error": "Not found"}
        s = p.stat()
        mod = datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return {"success": True, "output": (
            f"Path: {p.resolve()}\n"
            f"Size: {_fmt_size(s.st_size)}\n"
            f"Modified: {mod}\n"
            f"Created: {datetime.datetime.fromtimestamp(s.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Mode: {oct(s.st_mode)[-3:]}\n"
            f"Is file: {p.is_file()}\n"
            f"Is dir: {p.is_dir()}"
        )}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tail_file(filepath: str, lines: int = 10) -> dict:
    """Show last N lines of a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        tail = all_lines[-lines:]
        output = f"--- last {len(tail)} of {len(all_lines)} lines ---\n"
        output += "".join(tail)
        return {"success": True, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}


def head_file(filepath: str, lines: int = 10) -> dict:
    """Show first N lines of a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            head = [next(f) for _ in range(lines)]
        return {"success": True, "output": "".join(head)}
    except StopIteration:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            full = f.read()
        return {"success": True, "output": full}
    except Exception as e:
        return {"success": False, "error": str(e)}


def count_lines(filepath: str) -> dict:
    """Count lines, words, and characters in a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        lines = content.count("\n")
        words = len(content.split())
        chars = len(content)
        return {"success": True, "output": f"Lines: {lines}\nWords: {words}\nChars: {chars}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def diff_files(file_a: str, file_b: str) -> dict:
    """Compare two files line by line."""
    import difflib
    try:
        a = Path(file_a).read_text("utf-8", errors="replace").splitlines(keepends=True)
        b = Path(file_b).read_text("utf-8", errors="replace").splitlines(keepends=True)
        diff = list(difflib.unified_diff(a, b, fromfile=file_a, tofile=file_b, n=3))
        return {"success": True, "output": "".join(diff[:100]) + ("\n... (truncated)" if len(diff) > 100 else "")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Text / data tools ────────────────────────────────────────────

def format_json(text: str) -> dict:
    """Pretty-print a JSON string."""
    try:
        parsed = json.loads(text)
        return {"success": True, "output": json.dumps(parsed, indent=2, ensure_ascii=False)}
    except json.JSONDecodeError as e:
        return {"success": True, "output": f"Invalid JSON: {e}"}


def encode_base64(text: str) -> dict:
    """Base64-encode a string."""
    import base64
    try:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return {"success": True, "output": encoded}
    except Exception as e:
        return {"success": False, "error": str(e)}


def decode_base64(encoded: str) -> dict:
    """Decode a base64-encoded string."""
    import base64
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        return {"success": True, "output": decoded}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_uuid() -> dict:
    """Generate a random UUID v4."""
    import uuid
    return {"success": True, "output": str(uuid.uuid4())}


def hash_text(text: str, algorithm: str = "sha256") -> dict:
    """Hash a string using sha256, md5, or sha1."""
    import hashlib
    try:
        h = hashlib.new(algorithm, text.encode("utf-8"))
        return {"success": True, "output": h.hexdigest()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def count_tokens(text: str, model: str = "gpt-4") -> dict:
    """Estimate token count using tiktoken (falls back to 4-chars-per-token)."""
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        tokens = len(enc.encode(text))
        return {"success": True, "output": f"~{tokens} tokens ({model})"}
    except ImportError:
        rough = len(text) // 4
        return {"success": True, "output": f"~{rough} tokens (estimated, tiktoken not installed)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── System tools ─────────────────────────────────────────────────

def list_processes(name_filter: str = "") -> dict:
    """List running processes, optionally filtered by name."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                if name_filter and name_filter.lower() not in (info["name"] or "").lower():
                    continue
                procs.append(f"{info['pid']:>6}  {info['name'] or '?' :<30}  {info['cpu_percent'] or 0:>5.1f}%  {info['memory_percent'] or 0:>5.1f}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if not procs:
            return {"success": True, "output": "No matching processes"}
        header = f"{'PID':>6}  {'NAME':<30}  {'CPU':>5}  {'MEM':>5}"
        return {"success": True, "output": header + "\n" + "\n".join(sorted(procs))}
    except ImportError:
        return {"success": True, "output": "psutil not installed. Install with: pip install psutil"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def disk_usage(path: str = "/") -> dict:
    """Show disk usage for a given path."""
    import shutil
    try:
        total, used, free = shutil.disk_usage(path)
        pct = (used / total) * 100
        return {"success": True, "output": (
            f"Path: {path}\n"
            f"Total: {_fmt_size(total)}\n"
            f"Used:  {_fmt_size(used)} ({pct:.1f}%)\n"
            f"Free:  {_fmt_size(free)}"
        )}
    except Exception as e:
        return {"success": False, "error": str(e)}


def memory_usage() -> dict:
    """Show system memory usage."""
    import shutil
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {"success": True, "output": (
            f"Total: {_fmt_size(mem.total)}\n"
            f"Used:  {_fmt_size(mem.used)} ({mem.percent:.1f}%)\n"
            f"Free:  {_fmt_size(mem.available)}"
        )}
    except ImportError:
        return {"success": True, "output": "psutil not installed. Install with: pip install psutil"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def uptime() -> dict:
    """Show system uptime."""
    try:
        import psutil
        boot = datetime.datetime.fromtimestamp(psutil.boot_time())
        now = datetime.datetime.now()
        delta = now - boot
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, _ = divmod(rem, 60)
        return {"success": True, "output": f"Up {days}d {hours}h {minutes}m since {boot.strftime('%Y-%m-%d %H:%M:%S')}"}
    except ImportError:
        return {"success": True, "output": "psutil not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def ping_host(host: str, count: int = 3) -> dict:
    """Ping a host to check connectivity."""
    import subprocess
    try:
        flag = "-n" if os.name == "nt" else "-c"
        r = subprocess.run(["ping", flag, str(count), host], capture_output=True, text=True, timeout=15)
        output = r.stdout or r.stderr or ""
        return {"success": True, "output": output.strip()[:2000]}
    except subprocess.TimeoutExpired:
        return {"success": True, "output": f"Ping to {host} timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def http_get(url: str, timeout: int = 10) -> dict:
    """Perform a simple HTTP GET request."""
    try:
        import urllib.request
        r = urllib.request.urlopen(url, timeout=timeout)
        body = r.read().decode("utf-8", errors="replace")[:2000]
        return {"success": True, "output": f"Status: {r.status}\n\n{body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


TOOL_REGISTRY = {
    "web_search": {
        "fn": web_search,
        "desc": "Search the web for current information. ALWAYS use this when asked about recent events, facts you're unsure of, prices, news, or anything beyond your training data. Never guess — search first.",
    },
    "calculate": {
        "fn": calculate,
        "desc": "Evaluate a mathematical expression safely. ALWAYS use this for math instead of calculating in your head. Supports +, -, *, /, sqrt, abs, round, pi, e, sin, cos, log.",
    },
    "current_time": {
        "fn": current_time,
        "desc": "Get the current date and time. Use this instead of guessing what day it is or what time it is now.",
    },
    "fetch_url": {
        "fn": fetch_url,
        "desc": "Fetch content from a URL. Use this to verify what's actually at a link instead of guessing or describing what you think is there.",
    },
    "check_package_version": {
        "fn": check_package_version,
        "desc": "Check if a Python package is installed and what version. Use instead of guessing import availability or version numbers.",
    },
    "check_command": {
        "fn": check_command_exists,
        "desc": "Check if a CLI command or tool is available on the system. Use instead of assuming a tool exists.",
    },
    "validate_python": {
        "fn": validate_python_syntax,
        "desc": "Validate Python code syntax without executing it. Always use this before outputting code you want the user to run.",
    },
    "resolve_path": {
        "fn": resolve_path,
        "desc": "Resolve a file path — expand ~, env vars, check if it exists. Use instead of guessing file locations.",
    },
    "dns_lookup": {
        "fn": dns_lookup,
        "desc": "Look up DNS records for a hostname. Use instead of guessing IP addresses or whether a domain exists.",
    },
    "unit_convert": {
        "fn": unit_convert,
        "desc": "Convert between units (km/m/cm/mm, kg/g/lb, C/F/K, L/mL/gal, kmh/mph). Use instead of guessing conversions.",
    },
    "test_regex": {
        "fn": test_regex,
        "desc": "Test a regex pattern against a string and show matches. Use instead of guessing what a regex will match.",
    },
    "system_info": {
        "fn": system_info,
        "desc": "Get system information (OS, arch, Python version, CWD). Use instead of guessing the user's environment.",
    },
    "check_file_hash": {
        "fn": check_file_hash,
        "desc": "Compute a file hash (sha256, md5). Use to verify file integrity instead of guessing checksums.",
    },
    "what_is": {
        "fn": what_is,
        "desc": "Look up the dictionary definition of a word or term. Use instead of defining terms from memory.",
    },
    "check_port": {
        "fn": check_port,
        "desc": "Check if a port is open on a host. Use instead of guessing if a service is running on a remote server.",
    },
    "check_env_var": {
        "fn": check_env_var,
        "desc": "Check if an environment variable is set and return its value. Use instead of guessing env var names or values.",
    },
    "json_validate": {
        "fn": json_validate,
        "desc": "Parse and validate a JSON string. Use instead of guessing whether JSON is valid or what the structure looks like.",
    },
    "url_encode_decode": {
        "fn": url_encode_decode,
        "desc": "URL-encode or URL-decode a string. Use instead of guessing URL-encoded values.",
    },
    "copy_file": {
        "fn": copy_file,
        "desc": "Copy a file from source to destination. Always use this instead of guessing file paths.",
    },
    "move_file": {
        "fn": move_file,
        "desc": "Move or rename a file. Always use this instead of guessing file operations.",
    },
    "delete_file": {
        "fn": delete_file,
        "desc": "Delete a file permanently. Use to remove files safely.",
    },
    "list_dir": {
        "fn": list_dir,
        "desc": "List directory contents with file sizes and modification times.",
    },
    "find_files": {
        "fn": find_files,
        "desc": "Find files matching a glob pattern. Use instead of guessing file locations.",
    },
    "file_info": {
        "fn": file_info,
        "desc": "Get file metadata: size, modified time, permissions, full path.",
    },
    "tail_file": {
        "fn": tail_file,
        "desc": "Show the last N lines of a file. Use to inspect logs or large files.",
    },
    "head_file": {
        "fn": head_file,
        "desc": "Show the first N lines of a file.",
    },
    "count_lines": {
        "fn": count_lines,
        "desc": "Count lines, words, and characters in a file.",
    },
    "diff_files": {
        "fn": diff_files,
        "desc": "Compare two files line by line (unified diff). Use instead of guessing differences.",
    },
    "format_json": {
        "fn": format_json,
        "desc": "Pretty-print a JSON string with indentation.",
    },
    "encode_base64": {
        "fn": encode_base64,
        "desc": "Base64-encode a string.",
    },
    "decode_base64": {
        "fn": decode_base64,
        "desc": "Decode a Base64-encoded string back to text.",
    },
    "generate_uuid": {
        "fn": generate_uuid,
        "desc": "Generate a random UUID v4 string.",
    },
    "hash_text": {
        "fn": hash_text,
        "desc": "Hash a string using sha256 (default), md5, or sha1.",
    },
    "count_tokens": {
        "fn": count_tokens,
        "desc": "Estimate the token count of text using tiktoken. Use instead of guessing token usage.",
    },
    "list_processes": {
        "fn": list_processes,
        "desc": "List running system processes, optionally filtered by name.",
    },
    "disk_usage": {
        "fn": disk_usage,
        "desc": "Show disk usage statistics for a given path.",
    },
    "memory_usage": {
        "fn": memory_usage,
        "desc": "Show system memory usage (total, used, free, percent).",
    },
    "uptime": {
        "fn": uptime,
        "desc": "Show how long the system has been running since last boot.",
    },
    "ping_host": {
        "fn": ping_host,
        "desc": "Ping a host to check network connectivity.",
    },
    "http_get": {
        "fn": http_get,
        "desc": "Perform a simple HTTP GET request to a URL. Use instead of guessing what a URL returns.",
    },
}


def register_tools(r):
    for name, entry in TOOL_REGISTRY.items():
        r.register(name, entry["fn"], permission="always_allow", category="grounding")


def get_all_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())


def execute_tool(name: str, params: dict) -> dict:
    entry = TOOL_REGISTRY.get(name)
    if not entry:
        return {"success": False, "error": f"Unknown grounding tool: {name}"}
    try:
        return entry["fn"](**params)
    except TypeError as e:
        return {"success": False, "error": f"Invalid params for {name}: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
