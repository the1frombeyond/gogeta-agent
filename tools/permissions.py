"""Permission and approval framework for the unified tool platform.

Defines permission levels, approval workflows, and the central
``PermissionManager`` that gates tool execution.
"""

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PermissionLevel(enum.Enum):
    """Granularity of permission required to invoke a tool."""

    FREE = "free"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class ToolPermission:
    """Permission rules attached to a tool registration."""

    level: PermissionLevel = PermissionLevel.FREE
    requires_approval: bool = False
    approver_role: str = "user"
    allowed_contexts: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_minute: Optional[int] = None


class PermissionManager:
    """Central gate for tool execution and approval workflows.

    Decisions can be overridden by registering custom check functions
    per tool or per category.
    """

    def __init__(self):
        self._default_permissions: Dict[str, ToolPermission] = {}
        self._category_permissions: Dict[str, ToolPermission] = {}
        self._custom_checks: Dict[str, Callable[..., bool]] = {}
        self._approval_handlers: Dict[str, Callable[..., Awaitable[bool]]] = {}
        self._call_counts: Dict[str, List[float]] = {}

    def register_permission(self, tool_name: str, permission: ToolPermission) -> None:
        self._default_permissions[tool_name] = permission

    def register_category_permission(
        self, category: str, permission: ToolPermission
    ) -> None:
        self._category_permissions[category] = permission

    def register_custom_check(
        self, tool_name: str, check_fn: Callable[..., bool]
    ) -> None:
        self._custom_checks[tool_name] = check_fn

    def register_approval_handler(
        self, tool_name: str,
        handler: Callable[..., Awaitable[bool]],
    ) -> None:
        self._approval_handlers[tool_name] = handler

    def get_permission(
        self, tool_name: str, category: str = ""
    ) -> ToolPermission:
        perm = self._default_permissions.get(tool_name)
        if perm is not None:
            return perm
        if category:
            perm = self._category_permissions.get(category)
            if perm is not None:
                return perm
        return ToolPermission()

    def check_permission(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None,
        category: str = "",
    ) -> bool:
        custom = self._custom_checks.get(tool_name)
        if custom is not None:
            try:
                return bool(custom(context or {}))
            except Exception as exc:
                logger.warning(
                    "Custom permission check for '%s' raised: %s",
                    tool_name, exc,
                )
                return False

        perm = self.get_permission(tool_name, category)
        if perm.level == PermissionLevel.SYSTEM:
            return False

        if perm.rate_limit_per_minute is not None:
            import time
            now = time.monotonic()
            window_start = now - 60.0
            counts = self._call_counts.setdefault(tool_name, [])
            counts[:] = [ts for ts in counts if ts > window_start]
            if len(counts) >= perm.rate_limit_per_minute:
                logger.warning("Rate limit hit for '%s'", tool_name)
                return False

        return True

    async def request_approval(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None,
        category: str = "",
    ) -> bool:
        perm = self.get_permission(tool_name, category)
        if not perm.requires_approval:
            return True

        handler = self._approval_handlers.get(tool_name)
        if handler is not None:
            try:
                return await handler(context or {})
            except Exception as exc:
                logger.warning(
                    "Approval handler for '%s' raised: %s", tool_name, exc,
                )
                return False

        logger.info("Tool '%s' requires approval but no handler registered", tool_name)
        return False

    def record_call(self, tool_name: str) -> None:
        import time
        self._call_counts.setdefault(tool_name, []).append(time.monotonic())

    def reset_counts(self, tool_name: Optional[str] = None) -> None:
        if tool_name:
            self._call_counts.pop(tool_name, None)
        else:
            self._call_counts.clear()


permission_manager = PermissionManager()
