"""Project Intelligence subscriber — wires event bus to documentation files.

Listens for tool events, session events, and project updates to
automatically maintain ``project.md``, ``decision_log.md``,
``tasks.md``, and ``architecture.md``.

Usage::

    from core.intelligence import ProjectIntelligence

    pi = ProjectIntelligence()
    pi.start()
"""

import logging
import time
from pathlib import Path
from typing import Optional, Set

from core.events.bus import event_bus
from core.events.events import Event, EventType
from .project import ProjectManager
from .decisions import DecisionLog
from .tasks import TaskManager
from .architecture import ArchitectureManager

logger = logging.getLogger(__name__)

# File extensions that indicate project source code was modified
_SOURCE_EXTENSIONS: Set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java",
    ".kt", ".swift", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb",
    ".php", ".vue", ".svelte", ".css", ".scss", ".less", ".html",
    ".yaml", ".yml", ".toml", ".json", ".sql", ".md",
}


class ProjectIntelligence:
    """Listens to the event bus and updates project documentation files.

    Automatically wires up subscribers for:
    - ``TOOL_FINISHED`` — tracks file modifications, test results
    - ``TOOL_FAILED`` — tracks issues
    - ``SESSION_ENDED`` — session summary
    - ``PROJECT_UPDATED`` — explicit project state updates
    - ``REFLECTION_CREATED`` — ties into reflections
    """

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        auto_start: bool = False,
    ):
        if project_dir is None:
            project_dir = Path.cwd()
        self._dir = project_dir
        self.project = ProjectManager(project_dir / "project.md")
        self.decisions = DecisionLog(project_dir / "decision_log.md")
        self.tasks = TaskManager(project_dir / "tasks.md")
        self.architecture = ArchitectureManager(project_dir / "architecture.md")
        self._started = False
        self._files_modified_in_session: Set[str] = set()
        self._test_count: int = 0
        self._session_count: int = 0

        if auto_start:
            self.start()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished, priority=-20)
        event_bus.subscribe(EventType.TOOL_FAILED, self._on_tool_failed, priority=-20)
        event_bus.subscribe(EventType.PROJECT_UPDATED, self._on_project_updated, priority=-20)
        event_bus.subscribe(EventType.REFLECTION_CREATED, self._on_reflection_created, priority=-20)
        logger.info("Project Intelligence started — watching %s", self._dir)

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        event_bus.unsubscribe(EventType.TOOL_FINISHED, self._on_tool_finished)
        event_bus.unsubscribe(EventType.TOOL_FAILED, self._on_tool_failed)
        event_bus.unsubscribe(EventType.PROJECT_UPDATED, self._on_project_updated)
        event_bus.unsubscribe(EventType.REFLECTION_CREATED, self._on_reflection_created)
        logger.info("Project Intelligence stopped")

    @property
    def started(self) -> bool:
        return self._started

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_tool_finished(self, event: Event) -> None:
        data = event.data
        name = data.get("name", "")
        args = data.get("args", {})

        if name == "write_file" or name == "edit_file" or name == "patch":
            filepath = args.get("file_path", args.get("path", ""))
            if filepath:
                self._files_modified_in_session.add(filepath)
                self.project.append_to("files_modified", filepath)
                # Register architecture component from file path
                parts = filepath.replace("\\", "/").split("/")
                if len(parts) >= 2:
                    component = parts[0]
                    self.architecture.register_component(component)

        elif name == "run_tests":
            self._test_count += 1
            success = data.get("success", True)
            passed = args.get("passed", 0) if not success else "all"
            self.project.set("tests", f"{passed} passing (run #{self._test_count})")

        elif "complete" in name.lower() or "finish" in name.lower():
            self.tasks.complete_current()
            task_desc = args.get("description", args.get("task", name))
            self.project.add("completed", task_desc)

    def _on_tool_failed(self, event: Event) -> None:
        data = event.data
        name = data.get("name", "")
        error = data.get("error", "unknown error")
        self.project.add("issues", f"{name}: {error}")

    def _on_project_updated(self, event: Event) -> None:
        data = event.data
        for key, val in data.items():
            if key in ProjectManager.SECTION_HEADERS:
                if isinstance(val, list):
                    self.project.set_list(key, val)
                else:
                    self.project.set(key, str(val))

    def _on_reflection_created(self, event: Event) -> None:
        data = event.data
        title = data.get("title", "Reflection")
        body = data.get("body", "")
        if body:
            self.decisions.record(
                title=title,
                decision=body,
                context=data.get("context", ""),
                alternatives=data.get("alternatives", ""),
                tradeoffs=data.get("tradeoffs", ""),
            )
