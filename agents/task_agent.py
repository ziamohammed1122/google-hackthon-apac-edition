"""
Task Agent — Sub-agent responsible for task management.
Handles creating, listing, updating, and deleting tasks.
"""

import json
from typing import Dict, Optional
from .base_agent import BaseAgent
import database


class TaskAgent(BaseAgent):
    """Agent specialized in task management operations."""

    def __init__(self):
        super().__init__(
            name="TaskAgent",
            description="Manages tasks including creation, updates, listing, and deletion. Handles task prioritization and status tracking."
        )
        self._register_tools()

    def _register_tools(self):
        self.register_tool("create_task", self._create_task, "Create a new task")
        self.register_tool("list_tasks", self._list_tasks, "List tasks with optional filters")
        self.register_tool("get_task", self._get_task, "Get a specific task by ID")
        self.register_tool("update_task", self._update_task, "Update task fields")
        self.register_tool("delete_task", self._delete_task, "Delete a task")
        self.register_tool("complete_task", self._complete_task, "Mark a task as completed")

    async def _create_task(self, title: str, description: str = "", priority: str = "medium",
                           due_date: str = None, tags: list = None) -> Dict:
        return await database.create_task(title, description, priority, due_date, tags)

    async def _list_tasks(self, status: str = None, priority: str = None) -> list:
        return await database.list_tasks(status, priority)

    async def _get_task(self, task_id: int) -> Optional[Dict]:
        return await database.get_task(task_id)

    async def _update_task(self, task_id: int, **kwargs) -> Optional[Dict]:
        return await database.update_task(task_id, **kwargs)

    async def _delete_task(self, task_id: int) -> bool:
        return await database.delete_task(task_id)

    async def _complete_task(self, task_id: int) -> Optional[Dict]:
        return await database.update_task(task_id, status="completed")

    async def process(self, request: Dict) -> Dict:
        """Process a task-related request."""
        action = request.get("action", "")
        params = request.get("params", {})

        action_map = {
            "create": "create_task",
            "create_task": "create_task",
            "list": "list_tasks",
            "list_tasks": "list_tasks",
            "get": "get_task",
            "get_task": "get_task",
            "update": "update_task",
            "update_task": "update_task",
            "delete": "delete_task",
            "delete_task": "delete_task",
            "complete": "complete_task",
            "complete_task": "complete_task",
        }

        tool_name = action_map.get(action)
        if not tool_name:
            return {
                "success": False,
                "error": f"Unknown task action: {action}",
                "agent": self.name,
                "available_actions": list(action_map.keys())
            }

        result = await self.execute_tool(tool_name, **params)
        return {
            "success": "error" not in result if isinstance(result, dict) else True,
            "data": result,
            "agent": self.name,
            "action": action
        }
