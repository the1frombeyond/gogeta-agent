# Gogeta 3.0 Release Checklist

## Pre-Release

- [ ] All tests pass on `main`
  ```bash
  scripts/run_tests.sh
  ```
- [ ] No security vulnerabilities
  ```bash
  osv-scan --locked
  ```
- [ ] No secret leaks
  ```bash
  git log --all --diff-filter=A -- . | grep -iE '(api.?key|secret|token|password)'
  ```
- [ ] No `shell=True` in production code
  ```bash
  grep -rn "shell=True" tools/ agent/ gateway/ gogeta_cli/ --include="*.py" | grep -v test
  ```
- [ ] No broken imports
  ```bash
  python -c "import gogeta_cli.main; print('OK')"
  ```
- [ ] TUI builds
  ```bash
  cd ui-tui && npm run build
  ```
- [ ] Frontend assets built
  ```bash
  test -f gogeta_cli/tui_dist/entry.js
  ```
- [ ] Version bumped in `pyproject.toml` to 3.0.0
- [ ] Install scripts tested on clean environment
- [ ] `CHANGELOG.md` or release notes drafted

## Release

- [ ] Tag and push
  ```bash
  git tag -a v3.0.0 -m "Gogeta 3.0"
  git push origin v3.0.0
  ```
- [ ] GitHub Release published by CI
- [ ] Artifacts uploaded (install.ps1, install.sh, checksums.txt)
- [ ] PyPI package published (automatic via tag)

## Post-Release

- [ ] Verify one-command install from docs
  ```bash
  curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
  ```
- [ ] `gogeta doctor` passes on fresh install
- [ ] TUI launches (`gogeta --tui`)
- [ ] Gateway starts (`gogeta gateway`)
- [ ] Smoke test: basic conversation loop
- [ ] Smoke test: cron scheduler
- [ ] Smoke test: kanban board

## Rollback

If the release has critical issues:

```bash
git tag -d v3.0.0
git push origin :refs/tags/v3.0.0
```

Delete the GitHub Release from the web UI, then fix and re-release.
