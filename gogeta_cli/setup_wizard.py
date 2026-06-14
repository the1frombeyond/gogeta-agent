"""Interactive setup wizard for GOGETA — single file, no classes."""

import json
import os
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


# ── Provider data ──────────────────────────────────────────────────────────

PROVIDERS = [
    "Nous Portal",
    "OpenRouter",
    "Anthropic Claude",
    "OpenAI",
    "Google Gemini",
    "DeepSeek",
    "NVIDIA NIM",
    "Ollama",
    "AWS Bedrock",
    "Azure OpenAI",
    "Custom",
]

PROVIDER_DESCS = [
    "300+ models with bundled tool use",
    "Pay-per-use API aggregator",
    "Claude models via API key",
    "GPT models via API key",
    "Gemini models via AI Studio API",
    "V3, R1, coder models",
    "Nemotron models via build.nvidia.com",
    "Local open models via Ollama CLI",
    "Claude, Nova, Llama via AWS",
    "OpenAI or Anthropic on Azure",
    "Direct API endpoint",
]

PROVIDER_KEY_URLS = {
    "Nous Portal": "https://portal.nousresearch.com",
    "OpenRouter": "https://openrouter.ai/keys",
    "Anthropic Claude": "https://console.anthropic.com/",
    "OpenAI": "https://platform.openai.com/api-keys",
    "Google Gemini": "https://aistudio.google.com/",
    "DeepSeek": "https://platform.deepseek.com/api_keys",
    "NVIDIA NIM": "https://build.nvidia.com/",
    "AWS Bedrock": "https://aws.amazon.com/bedrock/",
    "Azure OpenAI": "https://portal.azure.com/",
    "Custom": "https://your-api-endpoint/",
}

PROVIDER_ENV_VARS = {
    "Nous Portal": "NOUS_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "Anthropic Claude": "ANTHROPIC_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Google Gemini": "GEMINI_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "NVIDIA NIM": "NVIDIA_API_KEY",
    "AWS Bedrock": "AWS_ACCESS_KEY_ID",
    "Azure OpenAI": "AZURE_OPENAI_KEY",
    "Custom": "CUSTOM_API_KEY",
}

# ── Messenger data ─────────────────────────────────────────────────────────

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

# ── Feature data ───────────────────────────────────────────────────────────

FEATURES = [
    "Web Search",
    "File System",
    "Code Execution",
    "Vision & Images",
    "Memory",
    "Web Browsing",
    "Voice / TTS",
    "Cron Jobs",
    "Delegation",
    "Git Integration",
    "Knowledge Base",
    "Plugin System",
]

FEATURE_DESCS = [
    "Search the web for real-time information",
    "Read, write, and manage files",
    "Run Python, Node, shell, and compiled code",
    "Analyze images and generate visuals",
    "Persist context across sessions",
    "Interactive browser automation",
    "Text-to-speech and speech-to-text",
    "Schedule recurring agent tasks",
    "Spawn sub-agents for parallel work",
    "Commit, diff, and manage repos",
    "Load custom skills and reference docs",
    "Extend with community plugins",
]


# ── Section: Provider ──────────────────────────────────────────────────────

def section_provider():
    print(f"  {DIM}── Step 1/4 ──{RST} {BOLD}Inference Provider{RST}\n")
    selected = multi_pick(PROVIDERS, "Choose your primary inference provider",
                          PROVIDER_DESCS, preselect=[0], select_all=False)
    if not selected:
        return PROVIDERS[0]
    idx = next(iter(selected))
    provider = PROVIDERS[idx]

    if provider not in ("Ollama", "LM Studio"):
        url = PROVIDER_KEY_URLS.get(provider, "https://console")
        env_var = PROVIDER_ENV_VARS.get(provider, "API_KEY")
        print(f"\n  {BOLD}{provider} API Key{RST}")
        print(f"  {DIM}Get one at: {CYAN}{url}{RST}")
        key = ask("Enter API key")
        if key:
            _save_env(env_var, key)

    return provider


# ── Section: Messaging ─────────────────────────────────────────────────────

def section_messaging():
    print(f"  {DIM}── Step 2/4 ──{RST} {BOLD}Messaging Platforms{RST}\n")
    print(f"  {DIM}Enable GOGETA on your messaging platforms.{RST}\n")

    selected = multi_pick(MESSENGER_APPS, "Select messengers", MESSENGER_DESCS)
    enabled = []

    for idx in sorted(selected):
        name = MESSENGER_APPS[idx]
        short = name.split("(")[0].strip().lower()
        enabled.append(short)
        print(f"\n  Configuring {name}:")

        if "slack" in short:
            token = ask("  Bot Token (xoxb-...)?")
            if token:
                _save_env("SLACK_BOT_TOKEN", token)

        elif "email" in short:
            imap = ask("  IMAP server?", "imap.gmail.com")
            user = ask("  Email address?")
            pwd = ask("  App password?")
            if imap:
                _set_config(["messengers", "email", "imap_server"], imap)
            if pwd:
                _save_env("EMAIL_APP_PASSWORD", pwd)

        elif "telegram" in short:
            token = ask("  Bot token (from @BotFather)?")
            if token:
                _save_env("TELEGRAM_BOT_TOKEN", token)

        elif "discord" in short:
            token = ask("  Bot token?")
            if token:
                _save_env("DISCORD_BOT_TOKEN", token)

        elif "twitter" in short or "x" in short:
            token = ask("  Bearer token?")
            if token:
                _save_env("TWITTER_BEARER_TOKEN", token)

        elif "whatsapp" in short:
            print(f"    WhatsApp Web Setup (no API key needed):")
            print(f"    Uses Playwright to automate WhatsApp Web.")
            print(f"    On first connect, a QR code appears.")
            if ask_yes_no("    Install Playwright + Chromium now?", True):
                _install_playwright()

    if enabled:
        print(f"\n  {GREEN}Messengers enabled:{RST} {', '.join(enabled)}")
    return enabled


# ── Section: Features ──────────────────────────────────────────────────────

def section_features():
    print(f"  {DIM}── Step 3/4 ──{RST} {BOLD}Features{RST}\n")
    print(f"  {DIM}Toggle which capabilities you want your agent to have.{RST}\n")

    selected = multi_pick(FEATURES, "Select features to enable", FEATURE_DESCS)
    features = [FEATURES[i] for i in sorted(selected)]
    return features


# ── Section: Lifeline ──────────────────────────────────────────────────────

def section_lifeline():
    print(f"  {DIM}── Step 4/4 ──{RST} {BOLD}Emergency Lifeline{RST}\n")
    print(f"  {DIM}If something goes wrong, how should the agent reach you?{RST}\n")
    phone = ask("Emergency phone (SMS)", "")
    email = ask("Emergency email", "")
    return phone or email or "none"


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


def write_config(provider, messengers, features, lifeline):
    home = _get_gogeta_home()
    home.mkdir(parents=True, exist_ok=True)

    yaml = [
        "# GOGETA Agent Configuration",
        f"# Generated by setup wizard",
        "",
        "provider:",
        f'  name: "{provider}"',
        "",
        "messengers:",
    ]
    for m in messengers:
        yaml.append(f'  - "{m}"')
    yaml.append("")
    yaml.append("features:")
    for f in features:
        yaml.append(f'  - "{f.lower().replace(chr(32), chr(95))}"')
    yaml.append("")
    yaml.append(f'lifeline: "{lifeline}"')
    yaml.append("")

    config_path = home / "config.yaml"
    config_path.write_text("\n".join(yaml), encoding="utf-8")
    return config_path


# ── Playwright install helper ──────────────────────────────────────────────

def _install_playwright():
    try:
        import playwright
    except ImportError:
        print("    Installing playwright...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    print("    Installing Chromium browser...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print(f"    {GREEN}Playwright + Chromium installed{RST}")


# ── Summary ────────────────────────────────────────────────────────────────

def summary(provider, messengers, features, lifeline, config_path):
    clear()
    print(f"{GOLD}{GOGETA_ART}{RST}")
    print(f"{GREEN}  Setup Complete!{RST}\n")
    print(f"  {BOLD}Provider:{RST}    {provider}")
    print(f"  {BOLD}Messengers:{RST}   {', '.join(messengers) if messengers else 'none'}")
    print(f"  {BOLD}Features:{RST}     {len(features)} enabled")
    print(f"  {BOLD}Lifeline:{RST}     {lifeline}")
    print(f"\n  {DIM}Config:{RST} {config_path}")
    print(f"  {DIM}Secrets:{RST} {_get_gogeta_home() / '.env'}")
    print(f"  {DIM}Run{RST}   `gogeta chat`{DIM} to start.{RST}\n")


# ── Entry point ────────────────────────────────────────────────────────────

def run():
    try:
        provider = section_provider()
        messengers = section_messaging()
        features = section_features()
        lifeline = section_lifeline()
        config_path = write_config(provider, messengers, features, lifeline)
        summary(provider, messengers, features, lifeline, config_path)
    except KeyboardInterrupt:
        clear()
        print(f"\n  {DIM}Setup cancelled.{RST}\n")
        sys.exit(1)


if __name__ == "__main__":
    run()
