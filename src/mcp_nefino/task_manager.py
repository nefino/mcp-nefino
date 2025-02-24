"""Task management for async operations."""

from dataclasses import dataclass
from datetime import datetime
import uuid
from typing import Any, Dict

from .client import NefinoClient
from .enums import TaskStatus


@dataclass
class Task:
    """Represents an async task."""
    id: str
    status: TaskStatus
    created_at: datetime
    result: Dict[str, Any] | None = None
    error: str | None = None


class TaskManager:
    """Manages async tasks."""
    
    def __init__(self):
        """Initialize task manager."""
        self.tasks: Dict[str, Task] = {}

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = Task(
            id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        return task_id

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        return self.tasks.get(task_id)

    async def execute_news_task(
        self,
        task_id: str,
        client: NefinoClient,
        **kwargs
    ) -> None:
        """Execute a news retrieval task."""
        task = self.tasks[task_id]
        try:
            result = await client.get_news(**kwargs)
            task.result = result
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
