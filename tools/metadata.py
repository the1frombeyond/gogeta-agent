"""Tool metadata model.

Holds versioning, dependency, cost-estimate, and categorization data
for every registered tool.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ToolMetadata:
    """Structured metadata for a registered tool."""

    version: str = "1.0.0"
    author: str = ""
    category: str = "uncategorized"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    cost_estimate: Optional[float] = None
    timeout_seconds: Optional[int] = None
    max_result_size_chars: Optional[int] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": list(self.tags),
            "dependencies": list(self.dependencies),
            "cost_estimate": self.cost_estimate,
            "timeout_seconds": self.timeout_seconds,
            "max_result_size_chars": self.max_result_size_chars,
            "description": self.description,
        }
