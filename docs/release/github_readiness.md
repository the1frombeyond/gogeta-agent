# Gogeta 3.0 — GitHub Readiness Checklist

## Repository Health

- [x] `README.md` describes what Gogeta is and how to install it
- [x] `LICENSE` file present (MIT)
- [x] `AGENTS.md` with comprehensive dev guide
- [x] `CONTRIBUTING.md` (if applicable)
- [x] `.gitignore` covers Python, Node, IDE artifacts
- [x] `pyproject.toml` with proper metadata (name, version, authors, license)

## CI/CD

- [x] Tests pass on main branch
- [x] Security scanning (OSV) configured
- [x] Linting configured (ruff)
- [x] PyPI publishing workflow configured
- [x] Docker publishing workflow configured
- [x] Release workflow configured (`release.yml`)

## Installation

- [x] `install.sh` at repository root for Linux/macOS
- [x] `install.ps1` at repository root for Windows
- [x] Both scripts available via raw GitHub URLs
- [x] `pip install gogeta-agent` works from PyPI

## Documentation

- [x] Installation guide
- [x] Upgrade guide
- [x] Release notes
- [x] Architecture overview (in AGENTS.md)

## Security

- [x] No hardcoded secrets or API keys
- [x] Dependencies pinned with upper bounds
- [x] No `shell=True` in production code
- [x] Installers don't bypass OS protections
- [x] All downloads from official sources only

## Release Artifacts

- [x] Checksums generated for install scripts
- [x] Installer scripts bundled in release
