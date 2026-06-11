# Next Session TODO

## 1. Push to GitHub
```bash
git remote add origin https://github.com/gogeta-agent/gogeta.git
git branch -M main
git push -u origin main
```

## 2. Create install.ps1
Create a PowerShell installation script at `scripts/install.ps1` (or root level since `gogeta_cli/scripts/` is gitignored).

The iex one-liner:
```powershell
iex (irm https://raw.githubusercontent.com/gogeta-agent/gogeta/main/scripts/install.ps1)
```

The script should:
- Check if Python 3.11+ is installed
- Install via `pip install gogeta-agent[all]` or `uv pip install gogeta-agent[all]`
- Or clone the repo and run `pip install -e ".[all,dev]"`
- Run `gogeta setup` post-install
- Handle admin elevation, PATH updates, etc.

## 3. Rewrite README.md — Humanizer
Run README.md through humanizer skill at moderate intensity (~50), casual-neutral tone. Hit the key differentiators:
- Why GOGETA is different
- Multi-platform, provider-agnostic, runs anywhere
- Skills, Genome, Lifeline
- Installation methods
- Quick start commands

## 4. Create GETTING_STARTED.md — Humanizer
Step-by-step tutorial for beginners:
- Install → `gogeta` → first chat
- `/model` to switch providers
- `/skills install` for skills
- `/cron add` for scheduled jobs
- `gogeta setup` for gateway config

## 5. Create INSTALL.md — Humanizer
Focused install guide covering all methods:
- One-liner (bash + PowerShell)
- pip / uv
- Docker
- Homebrew / Nix
- Windows native
- Post-install steps (`gogeta setup`, `gogeta doctor`)
