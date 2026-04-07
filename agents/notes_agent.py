"""
Notes Agent — Sub-agent responsible for notes and knowledge management.
Handles creating, searching, updating, and organizing notes.
"""

import json
from typing import Dict, Optional
from .base_agent import BaseAgent
import database


class NotesAgent(BaseAgent):
    """Agent specialized in notes and knowledge management."""

    def __init__(self):
        super().__init__(
            name="NotesAgent",
            description="Manages notes including creation, search, categorization, and organization."
        )
        self._register_tools()

    def _register_tools(self):
        self.register_tool("create_note", self._create_note, "Create a new note")
        self.register_tool("list_notes", self._list_notes, "List notes with optional filters")
        self.register_tool("get_note", self._get_note, "Get a specific note by ID")
        self.register_tool("update_note", self._update_note, "Update note fields")
        self.register_tool("delete_note", self._delete_note, "Delete a note")
        self.register_tool("search_notes", self._search_notes, "Search notes by keyword")
        self.register_tool("pin_note", self._pin_note, "Pin/unpin a note")

    async def _create_note(self, title: str, content: str = "", tags: list = None,
                           category: str = "general") -> Dict:
        return await database.create_note(title, content, tags, category)

    async def _list_notes(self, category: str = None, search: str = None) -> list:
        return await database.list_notes(category, search)

    async def _get_note(self, note_id: int) -> Optional[Dict]:
        return await database.get_note(note_id)

    async def _update_note(self, note_id: int, **kwargs) -> Optional[Dict]:
        return await database.update_note(note_id, **kwargs)

    async def _delete_note(self, note_id: int) -> bool:
        return await database.delete_note(note_id)

    async def _search_notes(self, query: str) -> list:
        return await database.search_notes(query)

    async def _pin_note(self, note_id: int, pinned: bool = True) -> Optional[Dict]:
        return await database.update_note(note_id, pinned=1 if pinned else 0)

    async def process(self, request: Dict) -> Dict:
        """Process a notes-related request."""
        action = request.get("action", "")
        params = request.get("params", {})

        action_map = {
            "create": "create_note",
            "create_note": "create_note",
            "list": "list_notes",
            "list_notes": "list_notes",
            "get": "get_note",
            "get_note": "get_note",
            "update": "update_note",
            "update_note": "update_note",
            "delete": "delete_note",
            "delete_note": "delete_note",
            "search": "search_notes",
            "search_notes": "search_notes",
            "pin": "pin_note",
            "pin_note": "pin_note",
        }

        tool_name = action_map.get(action)
        if not tool_name:
            return {
                "success": False,
                "error": f"Unknown notes action: {action}",
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
