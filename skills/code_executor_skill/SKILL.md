---
name: code_executor
description: Safe execution of Python, JavaScript, and shell commands in a sandboxed environment with timeout and resource limits
version: 1.0.0
---

# Code Executor Skill

## Description
Executes code snippets in Python, JavaScript, or shell with configurable timeout and resource safeguards. All executions run in subprocesses with automatic timeout enforcement.

## Triggers
- execute python code
- run javascript
- shell command
- run code snippet

## Usage
Use execute_python for Python code, execute_javascript for Node.js code, and execute_shell for shell commands. All methods accept a code string and return stdout/stderr with return code.
