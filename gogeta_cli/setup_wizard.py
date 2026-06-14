"""Interactive setup wizard for GOGETA — single file, no classes."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


# ── ASCII Art ──────────────────────────────────────────────────────────────

GOGETA_ART = r"""
   ____  ___   ____ _____ _____  _
  / ___|/ _ \ / ___| ____|_   _|/ \
 | |  _| | | | |  _|  _|   | | / _ \
 | |_| | |_| | |_| | |___  | |/ ___ \
  \____|\___/ \____|_____| |_/_/   \_\
"""

# ── ANSI helpers ───────────────────────────────────────────────────────────

GOLD = "\033[38;2;255;185;15m"
CYAN = "\033[38;2;0;200;255m"
GREEN = "\033[38;2;80;220;100m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[31m"
RST = "\033[22m\033[39m"


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def banner():
    clear()
    print(f"{GOLD}{GOGETA_ART}{RST}")
    print(f"{DIM}  ─── self-improving AI agent ───{RST}\n")


def ask(prompt_text, default=""):
    default_str = f" [{default}]" if default else ""
    val = input(f"  {BOLD}{prompt_text}{RST}{DIM}{default_str}{RST}: ").strip()
    return val or default


def ask_yes_no(prompt_text, default=True):
    hint = " [Y/n]" if default else " [y/N]"
    val = input(f"  {prompt_text}{hint}: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


# ── Cross-platform raw input ───────────────────────────────────────────────

def _getch_unix():
    import termios as _termios
    import tty as _tty
    fd = sys.stdin.fileno()
    old = _termios.tcgetattr(fd)
    try:
        _tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = ch + sys.stdin.read(2)
            return seq
        return ch
    finally:
        _termios.tcsetattr(fd, _termios.TCSADRAIN, old)


def _getch_win32():
    import msvcrt
    ch = msvcrt.getch()
    if ch == b"\xe0":
        seq = ch + msvcrt.getch()
        if seq == b"\xe0H":
            return "\x1b[A"
        if seq == b"\xe0P":
            return "\x1b[B"
        return seq.decode()
    return ch.decode()


_getch = _getch_win32 if sys.platform == "win32" else _getch_unix


# ── Multi-pick TUI ─────────────────────────────────────────────────────────

def _multi_pick_render(options, prompt, descriptions, selected, cursor):
    n = len(options)
    all_sel = (
        len(selected) == n - 1
        if options[0] == "[ Select All ]"
        else (len(selected) == n if n > 0 else False)
    )
    clear()
    print(f"{GOLD}{GOGETA_ART}{RST}")
    print()
    print(f"  {BOLD}{prompt}{RST}  {DIM}(Space=toggle, a=all, Enter=confirm){RST}\n")

    for i, opt in enumerate(options):
        if i == 0 and opt == "[ Select All ]":
            mark = f"{GREEN}●{RST}" if all_sel else f"{DIM}○{RST}"
        else:
            mark = f"{GREEN}●{RST}" if i in selected else f"{DIM}○{RST}"
        prefix = f"{GOLD}> {RST}" if i == cursor else "  "
        desc_text = f"  {DIM}{descriptions[i]}{RST}" if descriptions[i] else ""
        print(f"  {prefix} {mark} [{i+1:2d}] {opt}{desc_text}")

    real_count = n - (1 if options[0] == "[ Select All ]" else 0)
    print(f"\n  {DIM}{len(selected)}/{real_count} selected{RST}")
    sys.stdout.flush()


def _multi_pick_unix(options, prompt, descriptions, selected, cursor):
    _multi_pick_render(options, prompt, descriptions, selected, cursor)
    while True:
        ch = _getch()
        if ch == "\x1b[A":
            cursor = (cursor - 1) % len(options)
        elif ch == "\x1b[B":
            cursor = (cursor + 1) % len(options)
        elif ch == " ":
            if cursor == 0 and options[0] == "[ Select All ]":
                if len(selected) == len(options) - 1:
                    selected.clear()
                else:
                    selected = set(range(1, len(options)))
            elif cursor in selected:
                selected.remove(cursor)
            else:
                selected.add(cursor)
        elif ch in ("a", "A"):
            real_n = len(options) - (1 if options[0] == "[ Select All ]" else 0)
            if len(selected) == real_n:
                selected.clear()
            else:
                if options[0] == "[ Select All ]":
                    selected = set(range(1, len(options)))
                else:
                    selected = set(range(len(options)))
        elif ch in ("j",):
            cursor = (cursor + 1) % len(options)
        elif ch in ("k",):
            cursor = (cursor - 1) % len(options)
        elif ch in ("\r", "\n"):
            break
        elif ch == "\x03":
            raise KeyboardInterrupt
        _multi_pick_render(options, prompt, descriptions, selected, cursor)
    clear()
    return selected


def _multi_pick_win32(options, prompt, descriptions, selected, cursor):
    _multi_pick_render(options, prompt, descriptions, selected, cursor)
    while True:
        ch = _getch()
        if ch == "\x1b[A":
            cursor = (cursor - 1) % len(options)
        elif ch == "\x1b[B":
            cursor = (cursor + 1) % len(options)
        elif ch == " ":
            if cursor == 0 and options[0] == "[ Select All ]":
                if len(selected) == len(options) - 1:
                    selected.clear()
                else:
                    selected = set(range(1, len(options)))
            elif cursor in selected:
                selected.remove(cursor)
            else:
                selected.add(cursor)
        elif ch in ("a", "A"):
            real_n = len(options) - (1 if options[0] == "[ Select All ]" else 0)
            if len(selected) == real_n:
                selected.clear()
            else:
                if options[0] == "[ Select All ]":
                    selected = set(range(1, len(options)))
                else:
                    selected = set(range(len(options)))
        elif ch in ("j",):
            cursor = (cursor + 1) % len(options)
        elif ch in ("k",):
            cursor = (cursor - 1) % len(options)
        elif ch in ("\r", "\n"):
            break
        elif ch == "\x03":
            raise KeyboardInterrupt
        _multi_pick_render(options, prompt, descriptions, selected, cursor)
    clear()
    return selected


def multi_pick(options, prompt="Select", descriptions=None, preselect=None, select_all=True):
    desc = descriptions or [""] * len(options)

    if select_all:
        display_opts = ["[ Select All ]"] + list(options)
        display_desc = ["(toggle all items)"] + list(desc)
        if preselect:
            selected = {i + 1 for i in preselect}
        else:
            selected = set()
    else:
        display_opts = list(options)
        display_desc = list(desc)
        selected = set(preselect or [])

    cursor = 0

    if sys.platform == "win32":
        result = _multi_pick_win32(display_opts, prompt, display_desc, selected, cursor)
    else:
        result = _multi_pick_unix(display_opts, prompt, display_desc, selected, cursor)

    if select_all:
        return {i - 1 for i in result if i > 0}
    return result


# ── Identity ───────────────────────────────────────────────────────────────

def section_identity():
    banner()
    print(f"  {DIM}── Step 1/5 ──{RST} {BOLD}Identity{RST}\n")
    name = ask("What is your name?")
    agent_name = ask("What do you want to name your agent?", "GOGETA")
    print()
    return name, agent_name


# ── Provider ───────────────────────────────────────────────────────────────

PROVIDERS = [
    "Ollama",
    "OpenRouter",
    "Anthropic",
    "OpenAI",
    "Gemini",
    "Custom",
]

PROVIDER_DESCS = [
    "Local open models via Ollama CLI",
    "Pay-per-use API aggregator",
    "Claude models via API key",
    "GPT models via API key",
    "Gemini models via AI Studio API",
    "Direct API endpoint",
]

PROVIDER_KEY_URLS = {
    "OpenRouter": "https://openrouter.ai/keys",
    "Anthropic": "https://console.anthropic.com/",
    "OpenAI": "https://platform.openai.com/api-keys",
    "Gemini": "https://aistudio.google.com/",
}

PROVIDER_ENV_VARS = {
    "OpenRouter": "OPENROUTER_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Gemini": "GEMINI_API_KEY",
    "Custom": "CUSTOM_API_KEY",
}

DEFAULT_MODELS = {
    "OpenRouter": "openrouter/auto",
    "Anthropic": "claude-sonnet-4-20250514",
    "OpenAI": "gpt-4o",
    "Gemini": "gemini-2.5-flash",
}


def detect_ollama_models():
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        models = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line.strip():
                models.append(line.split()[0])
        return models
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def pull_ollama_model(model="llama3.2:3b"):
    print(f"\n  Pulling {model}...")
    subprocess.run(["ollama", "pull", model])


def section_provider():
    banner()
    print(f"  {DIM}── Step 2/5 ──{RST} {BOLD}Inference Provider{RST}\n")

    selected = multi_pick(PROVIDERS, "Pick provider", PROVIDER_DESCS, select_all=False)
    if not selected:
        return "Ollama", None, None, None

    idx = next(iter(selected))
    provider = PROVIDERS[idx]
    model = None
    api_key = None
    endpoint = None

    if provider == "Ollama":
        local = detect_ollama_models()
        if local:
            print(f"\n  {BOLD}Detected local Ollama models:{RST}")
            for m in local:
                print(f"    {DIM}●{RST} {m}")
            print()
            if ask_yes_no("Use a detected model?", True):
                if len(local) == 1:
                    model = local[0]
                    print(f"    Using {model}")
                else:
                    model = ask("Model name", local[0])
            else:
                if ask_yes_no("Pull llama3.2:3b?", True):
                    pull_ollama_model("llama3.2:3b")
                    model = "llama3.2:3b"
        else:
            print(f"\n  {DIM}No Ollama models detected.{RST}")
            if ask_yes_no("Pull llama3.2:3b?", True):
                pull_ollama_model("llama3.2:3b")
                model = "llama3.2:3b"
            else:
                model = ask("Model name", "llama3.2:3b")

    elif provider == "Custom":
        endpoint = ask("Endpoint URL", "https://api.openai.com/v1")
        model = ask("Model name", "gpt-4o")
        key = ask("API key")
        if key:
            api_key = key
            _save_env("CUSTOM_API_KEY", key)

    else:
        url = PROVIDER_KEY_URLS.get(provider, "https://console")
        env_var = PROVIDER_ENV_VARS.get(provider, "API_KEY")
        default_model = DEFAULT_MODELS.get(provider, "")
        print(f"\n  {BOLD}{provider}{RST}")
        print(f"  {DIM}Get an API key at: {CYAN}{url}{RST}")
        key = ask("API key")
        if key:
            api_key = key
            _save_env(env_var, key)
        model = ask("Default model", default_model)

    return provider, model, api_key, endpoint


# ── Messengers ─────────────────────────────────────────────────────────────

MESSENGER_APPS = [
    "WhatsApp (WhatsApp Web - no API key needed)",
    "Telegram (Bot API)",
    "Discord (Bot Token)",
    "Slack (Bolt/RTM)",
    "Signal (signal-cli bridge)",
    "Matrix (Matrix protocol)",
    "iMessage (Apple ecosystem)",
    "Twitter/X (Tweepy API)",
    "Email (IMAP/SMTP)",
]

MESSENGER_DESCS = [
    "WhatsApp Web multi-device auth via QR code",
    "Bot API integration with @BotFather token",
    "Rich presence bot with slash commands",
    "RTM and Events API with message scoping",
    "Local signal-cli bridge for encrypted messaging",
    "Decentralized protocol with room-based messaging",
    "Apple ecosystem messaging via macOS bridge",
    "Post tweets, search, read timeline via API v2",
    "Send and receive via IMAP/SMTP",
]


def section_messaging():
    banner()
    print(f"  {DIM}── Step 3/5 ──{RST} {BOLD}Messaging Platforms{RST}\n")

    selected = multi_pick(MESSENGER_APPS, "Select messengers", MESSENGER_DESCS)
    enabled = []

    for idx in sorted(selected):
        name = MESSENGER_APPS[idx]
        short = name.split("(")[0].strip().lower()
        enabled.append(short)
        print(f"\n  Configuring {name}:")

        if "telegram" in short:
            token = ask("  Bot token (from @BotFather)?")
            if token:
                _save_env("TELEGRAM_BOT_TOKEN", token)

        elif "discord" in short:
            token = ask("  Bot token?")
            if token:
                _save_env("DISCORD_BOT_TOKEN", token)

        elif "slack" in short:
            token = ask("  Bot Token (xoxb-...)?")
            if token:
                _save_env("SLACK_BOT_TOKEN", token)

        elif "signal" in short:
            phone = ask("  Phone number (E.164)?", "+1234567890")
            if phone:
                _set_config(["messengers", "signal", "phone"], phone)

        elif "matrix" in short:
            homeserver = ask("  Homeserver URL?", "https://matrix.org")
            user = ask("  Username?")
            if homeserver:
                _set_config(["messengers", "matrix", "homeserver"], homeserver)

        elif "whatsapp" in short:
            print("    WhatsApp Web Setup (no API key needed):")
            print("    Uses Playwright to automate WhatsApp Web.")
            print("    On first connect, a QR code appears.")
            if ask_yes_no("    Install Playwright + Chromium now?", True):
                _install_playwright()

        elif "twitter" in short or "x" in short:
            token = ask("  Bearer token?")
            if token:
                _save_env("TWITTER_BEARER_TOKEN", token)

        elif "email" in short:
            imap = ask("  IMAP server?", "imap.gmail.com")
            user = ask("  Email address?")
            pwd = ask("  App password?")
            if imap:
                _set_config(["messengers", "email", "imap_server"], imap)
            if pwd:
                _save_env("EMAIL_APP_PASSWORD", pwd)

        elif "imessage" in short:
            print("    iMessage uses macOS bridge.")
            print("    No API key needed on macOS.")

    if enabled:
        print(f"\n  {GREEN}Messengers enabled:{RST} {', '.join(enabled)}")
    return enabled


# ── North Star Features ────────────────────────────────────────────────────

NORTH_STAR_FEATURES = [
    "Architecture Enforcement",
    "Cost Intelligence",
    "Quality Gates",
    "Autonomous Improvement",
    "Smart Routing",
]

NORTH_STAR_DESCS = [
    "Enforce coding standards and patterns automatically",
    "Optimize spend with model routing and budget tracking",
    "Automated testing gates before every commit/merge",
    "Self-improvement loop that learns from past sessions",
    "Route tasks to the best model for each job",
]


def section_features():
    banner()
    print(f"  {DIM}── Step 4/5 ──{RST} {BOLD}North Star Features{RST}\n")
    print(f"  {DIM}Pick the agent's core capabilities.{RST}\n")

    selected = multi_pick(NORTH_STAR_FEATURES, "Select North Star features", NORTH_STAR_DESCS)
    features = [NORTH_STAR_FEATURES[i] for i in sorted(selected)]

    print()
    extras = {}
    extras["vision"] = ask_yes_no("  Enable vision (screen parsing)?", True)
    extras["voice"] = ask_yes_no("  Enable voice engine?", False)
    extras["auto_pilot"] = ask_yes_no("  Enable auto-pilot by default?", False)
    extras["memory"] = ask_yes_no("  Enable persistent memory engines?", True)
    extras["self_improve"] = ask_yes_no("  Enable self-improvement loop?", True)

    return features, extras


# ── Lifeline / Soul ────────────────────────────────────────────────────────

PERSONALITY_QUESTIONS = [
    ("Tone", "How should the agent speak to you?",
     ["Direct and concise", "Friendly and warm", "Professional and formal", "Witty and sarcastic"]),
    ("Boundaries", "How much autonomy should the agent have?",
     ["Ask before everything", "Suggest then act", "Act then report", "Full autonomy"]),
    ("Expertise", "What domain should the agent specialize in?",
     ["General purpose", "Software engineering", "Data science", "DevOps", "Research"]),
    ("Risk", "How risk-tolerant should the agent be?",
     ["Extremely cautious", "Moderate caution", "Balanced", "Take calculated risks"]),
]


def pick_from_list(prompt_text, options):
    print(f"\n  {BOLD}{prompt_text}{RST}")
    for i, opt in enumerate(options):
        print(f"    [{i+1}] {opt}")
    val = input(f"  {DIM}Choice [1-{len(options)}]{RST}: ").strip()
    try:
        idx = int(val) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[0]


def section_lifeline():
    banner()
    print(f"  {DIM}── Step 5/5 ──{RST} {BOLD}Agent Personality & Lifeline{RST}\n")
    print(f"  {DIM}Set up how the agent should behave and how it reaches you.{RST}\n")

    soul = {}
    for key, question, options in PERSONALITY_QUESTIONS:
        soul[key.lower()] = pick_from_list(question, options)

    print(f"\n  {DIM}Emergency contact (lifeline):{RST}")
    phone = ask("  Phone (SMS)", "")
    email = ask("  Email", "")

    return soul, phone or email or "none"


# ── Config persistence ─────────────────────────────────────────────────────

def _get_gogeta_home():
    return Path(os.environ.get("GOGETA_HOME", Path.home() / ".gogeta"))


def _save_env(key, value):
    home = _get_gogeta_home()
    env_path = home / ".env"
    home.mkdir(parents=True, exist_ok=True)
    existing = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip().strip('"')
    existing[key] = value
    lines = [f'{k}="{v}"' for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n")


def _set_config(keys, value):
    home = _get_gogeta_home()
    config_path = home / "config.json"
    home.mkdir(parents=True, exist_ok=True)
    data = {}
    if config_path.exists():
        data = json.loads(config_path.read_text())
    target = data
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value
    config_path.write_text(json.dumps(data, indent=2))


def write_config(provider, model, endpoint, messengers, features, extras, soul, lifeline, user_name, agent_name):
    home = _get_gogeta_home()
    home.mkdir(parents=True, exist_ok=True)

    lines = [
        "# GOGETA Agent Configuration",
        f"# Generated by setup wizard",
        "",
        "agent:",
        f'  name: "{agent_name}"',
        "",
        "user:",
        f'  name: "{user_name}"',
        "",
        "provider:",
        f'  name: "{provider}"',
    ]
    if model:
        lines.append(f'  model: "{model}"')
    if endpoint:
        lines.append(f'  endpoint: "{endpoint}"')
    lines.append("")
    lines.append("messengers:")
    for m in messengers:
        lines.append(f'  - "{m}"')
    lines.append("")
    lines.append("features:")
    for f in features:
        lines.append(f'  - "{f.lower().replace(chr(32), chr(95))}"')
    if extras.get("vision"):
        lines.append('  - "vision"')
    if extras.get("voice"):
        lines.append('  - "voice"')
    if extras.get("auto_pilot"):
        lines.append('  - "auto_pilot"')
    if extras.get("memory"):
        lines.append('  - "memory"')
    if extras.get("self_improve"):
        lines.append('  - "self_improvement_loop"')
    lines.append("")
    lines.append("personality:")
    for key, val in soul.items():
        lines.append(f'  {key}: "{val}"')
    lines.append("")
    lines.append(f'lifeline: "{lifeline}"')
    lines.append("")

    config_path = home / "config.yaml"
    config_path.write_text("\n".join(lines), encoding="utf-8")
    return config_path


# ── Playwright install helper ──────────────────────────────────────────────

def _install_playwright():
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("    Installing playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    print("    Installing Chromium browser...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print(f"    {GREEN}Playwright + Chromium installed{RST}")


# ── Summary ────────────────────────────────────────────────────────────────

def run():
    try:
        user_name, agent_name = section_identity()

        provider, model, api_key, endpoint = section_provider()

        messengers = section_messaging()

        features, extras = section_features()

        soul, lifeline = section_lifeline()

        config_path = write_config(
            provider, model, endpoint,
            messengers, features, extras,
            soul, lifeline, user_name, agent_name,
        )

        clear()
        print(f"{GOLD}{GOGETA_ART}{RST}")
        print(f"{GREEN}  Setup Complete!{RST}\n")
        print(f"  {BOLD}Agent:{RST}       {agent_name}")
        print(f"  {BOLD}User:{RST}        {user_name}")
        print(f"  {BOLD}Provider:{RST}    {provider}")
        if model:
            print(f"  {BOLD}Model:{RST}       {model}")
        print(f"  {BOLD}Messengers:{RST}   {', '.join(messengers) if messengers else 'none'}")
        print(f"  {BOLD}Features:{RST}     {len(features)} north star + {' '.join(k for k, v in extras.items() if v)}")
        print(f"\n  {DIM}Config:{RST} {config_path}")
        print(f"  {DIM}Secrets:{RST} {_get_gogeta_home() / '.env'}")
        print(f"  {DIM}Run{RST}   `gogeta chat`{DIM} to start.{RST}\n")

    except KeyboardInterrupt:
        clear()
        print(f"\n  {DIM}Setup cancelled.{RST}\n")
        sys.exit(1)


if __name__ == "__main__":
    run()
