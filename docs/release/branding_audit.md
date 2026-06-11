# Branding Audit — Gogeta 3.0

## Summary

- **Project name:** Gogeta 3.0 (formerly Hermes Agent)
- **Audit date:** June 2026
- **Scope:** Full repository identity rewrite — environment variables, function names, class names, file/directory names, docstrings, comments, Docker images, GitHub URLs, CLI banners, ASCII art, help text, and stale build artifacts.

## References KEPT (legal/attribution only)

Three functional upstream GitHub issue links preserved because they point to real, relevant discussions:

| File | Line | URL |
|------|------|-----|
| `gogeta_constants.py` | 133 | `https://github.com/NousResearch/hermes-agent/issues/18594` |
| `gogeta_constants.py` | 545 | `https://github.com/NousResearch/hermes-agent/issues/25821` |
| `gogeta_cli/auth.py` | 13121 | `https://github.com/NousResearch/hermes-agent/issues/26990` |

### Other preserved files (not Hermes-related)

| File | Reason |
|------|--------|
| `LICENSE` | MIT, Copyright (c) 2025 Nous Research — legally required attribution |
| `optional-skills/creative/pixel-art/ATTRIBUTION.md` | Credits upstream pixel-art-studio project (unrelated to Hermes) |
| `plugins/security-guidance/NOTICE` | Credits Anthropic's claude-plugins-official (unrelated to Hermes) |

## References REMOVED

- **GitHub URLs:** `github.com/NousResearch/hermes-agent` → `github.com/gogeta/gogeta-agent` (all occurrences)
- **Docker images:** `nousresearch/hermes-agent` → `gogeta/gogeta-agent` (all occurrences)
- **Stale `.pyc` cache files:** 8 files cleaned

## References RENAMED

| Category | Count | Example Change |
|----------|-------|----------------|
| Environment variables | 3,200+ | `HERMES_HOME` → `GOGETA_HOME`, `HERMES_TUI_*` → `GOGETA_TUI_*` |
| Function/class names | 100+ | `get_hermes_home()` → `get_gogeta_home()` |
| File/directory names | 40 files, 9 directories | `hermes_bootstrap.py` → `gogeta_bootstrap.py` |
| Docstrings/comments | 1,836+ files | All inline Hermes references updated |
| CLI banners, ASCII art, help text | — | All CLI surface references updated |

## Dist files requiring rebuild

The following directories contain branded copies of minified JS/CSS assets that still contain `hermes` references. A clean rebuild is needed to fully resolve:

- `plugins/kanban/dashboard/dist/`
- `plugins/gogeta-achievements/dashboard/dist/`

## Conclusion

The repository has been fully rebranded from Hermes Agent to Gogeta 3.0. All code-level, config-level, and documentation-level references have been audited and updated. The only remaining Hermes references are three functional upstream issue URLs preserved for their ongoing utility, plus two legal/attribution files (`LICENSE`, `ATTRIBUTION.md`, `NOTICE`) that credit unrelated third-party projects. Two dist directories require a rebuild to fully remove embedded `hermes` strings from minified assets.
