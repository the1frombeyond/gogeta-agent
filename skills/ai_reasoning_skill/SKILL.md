---
name: ai_reasoning
description: Direct access to local LLM intelligence via Ollama for pure reasoning, brainstorming, and creative tasks.
version: 1.0.0
---

# AI Reasoning Skill

This skill provides a direct channel to the local LLM "brain" for tasks that require intelligence but no external tools.

## Instructions
1. Use this skill when the user asks for brainstorming, creative writing, or complex reasoning.
2. Default model is `llama3`.
3. For fast responses, consider using `mistral`.
4. For critical validation, use the `qwen2.5` voice.

## Engine
- **Ollama API**: `http://localhost:11434/api/generate`
