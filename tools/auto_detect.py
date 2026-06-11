"""Auto-detect local LLM providers and hardware to recommend best model."""

import json
import os
import platform
import subprocess
import sys
import urllib.request
import urllib.error

GOGETA_HOME = os.environ.get("GOGETA_HOME", os.path.join(os.path.expanduser("~"), ".gogeta"))
REPORT_FILE = os.path.join(GOGETA_HOME, "auto_detect_report.json")


def _http_get(url: str, timeout: int = 5):
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        if resp.status == 200:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


def _nvidia_vram():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free,memory.used",
             "--format=csv,noheader,nounits"],
            timeout=10, stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        if out:
            parts = out.split(",")
            if len(parts) >= 3:
                return {"total_gb": int(parts[0].strip()) / 1024,
                        "free_gb": int(parts[1].strip()) / 1024,
                        "used_gb": int(parts[2].strip()) / 1024}
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _nvidia_gpu_name():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            timeout=10, stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return out.split(",")[0].strip() if out else None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _detect_gpu():
    vram = _nvidia_vram()
    if vram:
        name = _nvidia_gpu_name() or "NVIDIA GPU"
        return {"type": "nvidia", "name": name, **vram}
    is_apple_silicon = platform.machine() == "arm64" and platform.system() == "Darwin"
    if is_apple_silicon:
        return {"type": "apple_silicon", "name": "Apple Silicon"}
    return {"type": "none", "name": "No GPU detected (CPU only)"}


def _detect_ollama():
    data = _http_get("http://localhost:11434/api/tags")
    if data:
        try:
            parsed = json.loads(data)
            models = [m["name"] for m in parsed.get("models", [])]
            return {"running": True, "models": models}
        except (json.JSONDecodeError, KeyError, TypeError):
            return {"running": True, "models": []}
    return {"running": False, "models": []}


def _detect_lm_studio():
    data = _http_get("http://localhost:1234/v1/models")
    if data:
        try:
            parsed = json.loads(data)
            models = [m["id"] for m in parsed.get("data", [])]
            return {"running": True, "models": models}
        except (json.JSONDecodeError, KeyError, TypeError):
            return {"running": True, "models": []}
    return {"running": False, "models": []}


def _detect_huggingface_tgi():
    data = _http_get("http://localhost:8080/v1/models")
    if data:
        try:
            parsed = json.loads(data)
            models = [m["id"] for m in parsed.get("data", [])]
            return {"running": True, "models": models}
        except (json.JSONDecodeError, KeyError, TypeError):
            return {"running": True, "models": []}
    return {"running": False, "models": []}


def _detect_providers():
    return {
        "ollama": _detect_ollama(),
        "lm_studio": _detect_lm_studio(),
        "huggingface_tgi": _detect_huggingface_tgi(),
    }


def _system_specs():
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cpu_cores = psutil.cpu_count(logical=True)
        cpu_phys = psutil.cpu_count(logical=False) or cpu_cores
    except Exception:
        ram_gb = 8
        cpu_cores = 4
        cpu_phys = 4
    return {
        "ram_gb": round(ram_gb, 1),
        "cpu_cores": cpu_cores,
        "cpu_physical": cpu_phys,
        "os": platform.system(),
        "arch": platform.machine(),
    }


def _recommend(providers, gpu, specs):
    ram_gb = specs["ram_gb"]
    running = []

    if providers["ollama"]["running"]:
        running.append("ollama")
    if providers["lm_studio"]["running"]:
        running.append("lm_studio")
    if providers["huggingface_tgi"]["running"]:
        running.append("huggingface_tgi")

    recommendation = {
        "provider": None,
        "model": None,
        "quantization": None,
        "reasoning": "",
        "install_guide": None,
    }

    if running:
        preferred = running[0]
        recommendation["reasoning"] = f"Detected running provider: {preferred}"

        has_models = []
        for p in running:
            has_models.extend(providers[p].get("models", []))

        if preferred == "ollama":
            available_models = providers["ollama"]["models"]
            if available_models:
                recommendation["provider"] = "ollama"
                recommendation["model"] = available_models[0]
                recommendation["reasoning"] += f" using first available model: {available_models[0]}"
            else:
                recommendation["provider"] = "ollama"
                recommendation["model"] = _recommend_model_name(gpu, ram_gb)
                recommendation["reasoning"] += f". No models installed yet; recommend pulling: {recommendation['model']}"
                recommendation["install_guide"] = f"ollama pull {recommendation['model']}"

        elif preferred == "lm_studio":
            models = providers["lm_studio"]["models"]
            recommendation["provider"] = "lm_studio"
            recommendation["model"] = models[0] if models else _recommend_model_name(gpu, ram_gb)
            recommendation["reasoning"] += f" using model: {recommendation['model']}"

        elif preferred == "huggingface_tgi":
            models = providers["huggingface_tgi"]["models"]
            recommendation["provider"] = "huggingface_tgi"
            recommendation["model"] = models[0] if models else _recommend_model_name(gpu, ram_gb)
            recommendation["reasoning"] += f" using model: {recommendation['model']}"

    else:
        recommendation["reasoning"] = "No running local providers detected. "
        model_name = _recommend_model_name(gpu, ram_gb)
        recommendation["install_guide"] = f"Install Ollama from https://ollama.com then: ollama pull {model_name}"
        recommendation["reasoning"] += f"Recommend installing Ollama and pulling {model_name}"

    return recommendation


def _recommend_model_name(gpu, ram_gb):
    vram_gb = gpu.get("total_gb") if gpu["type"] == "nvidia" else 0

    if gpu["type"] == "nvidia":
        if vram_gb >= 80:
            return "command-r-plus:104b-q4_K_M"
        elif vram_gb >= 48:
            return "dolphin-mixtral:8x22b-q4_K_M"
        elif vram_gb >= 24:
            return "qwen2.5:32b-instruct-q4_K_M"
        elif vram_gb >= 16:
            return "qwen2.5:14b-instruct-q4_K_M"
        elif vram_gb >= 8:
            return "llama3.1:8b-instruct-q4_K_M"
        elif vram_gb >= 4:
            return "phi3:mini-4k-instruct-q4_K_M"
        else:
            return "tinyllama:1.1b"

    if gpu["type"] == "apple_silicon":
        if ram_gb >= 64:
            return "qwen2.5:32b-instruct-q4_K_M"
        elif ram_gb >= 32:
            return "qwen2.5:14b-instruct-q4_K_M"
        elif ram_gb >= 16:
            return "llama3.1:8b-instruct-q4_K_M"
        else:
            return "phi3:mini-4k-instruct-q4_K_M"

    if ram_gb >= 32:
        return "qwen2.5:14b-instruct-q4_K_M"
    elif ram_gb >= 16:
        return "llama3.1:8b-instruct-q4_K_M"
    elif ram_gb >= 8:
        return "phi3:mini-4k-instruct-q4_K_M"
    else:
        return "tinyllama:1.1b"


def run_detect() -> dict:
    """Run full auto-detect and return structured report."""

    os.makedirs(GOGETA_HOME, exist_ok=True)

    specs = _system_specs()
    gpu = _detect_gpu()
    providers = _detect_providers()
    recommendation = _recommend(providers, gpu, specs)

    report = {
        "system": specs,
        "gpu": gpu,
        "providers": providers,
        "recommendation": recommendation,
    }

    try:
        with open(REPORT_FILE, "w") as f:
            json.dump(report, f, indent=2)
    except (OSError, PermissionError):
        pass

    return report


def print_report(report: dict):
    """Print a human-friendly report of auto-detect results."""
    sys_info = report["system"]
    gpu = report["gpu"]
    providers = report["providers"]
    rec = report["recommendation"]

    print("=" * 60)
    print("  gogeta auto-detect report")
    print("=" * 60)

    print(f"\n  System:")
    print(f"    OS:     {sys_info['os']} ({sys_info['arch']})")
    print(f"    RAM:    {sys_info['ram_gb']} GB")
    print(f"    CPU:    {sys_info['cpu_physical']} physical / {sys_info['cpu_cores']} logical cores")

    print(f"\n  GPU:")
    if gpu["type"] == "nvidia":
        print(f"    {gpu['name']} ({gpu['total_gb']:.0f} GB VRAM)")
    elif gpu["type"] == "apple_silicon":
        print(f"    Apple Silicon (shared memory)")
    else:
        print(f"    CPU only")

    print(f"\n  Local Providers:")
    for name, info in providers.items():
        status = "running" if info["running"] else "not found"
        models = info.get("models", [])
        if models:
            print(f"    {name}: {status} ({len(models)} models)")
        else:
            print(f"    {name}: {status}")

    print(f"\n  Recommendation:")
    if rec["provider"]:
        print(f"    Provider: {rec['provider']}")
        print(f"    Model:    {rec['model']}")
    elif rec["install_guide"]:
        print(f"    No provider running")
    print(f"    Reason: {rec['reasoning']}")
    if rec["install_guide"]:
        print(f"\n    To get started: {rec['install_guide']}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    r = run_detect()
    print_report(r)
    # Output JSON for scripting
    print(f"\nJSON: {json.dumps(r)}")
