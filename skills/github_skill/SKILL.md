---
name: github
description: Integrated GitHub management skill using the gh CLI for PRs, issues, and workflow monitoring.
version: 1.0.0
---

# GitHub Skill

This skill allows JARVIS to interact with GitHub repositories, monitor CI/CD pipelines, and manage pull requests.

## Instructions
1. Use `gh pr checks` to monitor CI status.
2. Use `gh run list` and `gh run view` for troubleshooting failed workflow runs.
3. For complex data retrieval, use `gh api` with `--jq` filters.
4. **Context**: Always specify `--repo owner/repo` when working outside of a local git directory.

## Common Commands
- `gh pr list --limit 10`: List recent pull requests.
- `gh issue status`: Show status of issues assigned to you.
- `gh run view --log-failed`: Quickly find the cause of a CI failure.

## Requirements
- GitHub CLI (`gh`) must be installed and authenticated (`gh auth login`).
