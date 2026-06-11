---
name: mcp_builder
description: Guide and automation for creating high-quality MCP (Model Context Protocol) servers. Includes a tool to scan local apps and auto-generate MCP server code.
version: 1.0.0
---

# MCP Builder Skill

This skill enables JARVIS to create, evaluate, and auto-generate Model Context Protocol (MCP) servers. An MCP server provides tools that allow LLMs to access external services and APIs.

## 🚀 High-Level Workflow
1. **Deep Research and Planning**: Build for workflows, optimize for limited context, design actionable error messages.
2. **Implementation**: Use FastMCP (Python) or MCP TypeScript SDK. Implement core infrastructure first, then tools systematically.
3. **Review and Refine**: Check for DRY, composability, and error handling. Test in `tmux` or outside the main process.
4. **Create Evaluations**: Test effectiveness with 10 complex, realistic, verifable, read-only questions formatted in XML.

## 🔍 Auto-Generation (App Scanner)
This skill includes an automated scanner that looks for common local applications or developer tools and automatically generates a skeleton FastMCP server to connect to them.

**Usage**:
`python skills/mcp_builder_skill/mcp_scanner.py`

## References
- MCP Protocol: `https://modelcontextprotocol.io/llms-full.txt`
- Python SDK: `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- TypeScript SDK: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
