---
name: file_manager
description: Intelligent local file management skill for organizing, reading, and moving documents in the JARVIS workspace.
version: 1.1.0
---

# File Manager Skill

This skill allows JARVIS to manage your local filesystem safely and efficiently.

## Instructions
1. Use `list` to see contents of the current directory.
2. Use `read` followed by a filename to view the content of a file.
3. Use `organize` to automatically categorize files into subfolders based on their extension.
4. Always double-check before performing destructive actions (delete/remove).

## Safety
- Operations are restricted to the local project workspace.
- No root or system-level deletions allowed.
