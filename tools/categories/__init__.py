"""Organized category tool packages.

Each module in this directory provides tool registrations for a functional
category (file operations, code analysis, memory, gateway, MCP, skills,
lifeline, project intelligence, etc.).

Modules self-register via ``registry.register()`` at module level.
Discovery is handled by ``tools.discovery.discover_category_tools()``.
"""
