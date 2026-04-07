"""
Calendar Agent — Sub-agent responsible for calendar/schedule management.
Handles creating, listing, updating, and deleting calendar events.
"""

import json
from typing import Dict, Optional
from .base_agent import BaseAgent
import database


class CalendarAgent(BaseAgent):
    """Agent specialized in calendar and scheduling operations."""

    def __init__(self):
        super().__init__(
            name="CalendarAgent",
            description="Manages calendar events including scheduling, rescheduling, and conflict detection."
        )
        self._register_tools()

    def _register_tools(self):
        self.register_tool("create_event", self._create_event, "Create a new calendar event")
        self.register_tool("list_events", self._list_events, "List events with optional date range filter")
        self.register_tool("get_event", self._get_event, "Get a specific event by ID")
        self.register_tool("update_event", self._update_event, "Update event fields")
        self.register_tool("delete_event", self._delete_event, "Delete an event")
        self.register_tool("check_conflicts", self._check_conflicts, "Check for scheduling conflicts")

    async def _create_event(self, title: str, start_time: str, end_time: str = None,
                            description: str = "", location: str = "", attendees: list = None) -> Dict:
        # Check for conflicts first
        conflicts = await self._check_conflicts(start_time=start_time, end_time=end_time)
        event = await database.create_event(title, start_time, end_time, description, location, attendees)
        if conflicts.get("has_conflicts"):
            event["warnings"] = [f"Potential conflict with: {c['title']}" for c in conflicts.get("conflicts", [])]
        return event

    async def _list_events(self, start_after: str = None, start_before: str = None) -> list:
        return await database.list_events(start_after, start_before)

    async def _get_event(self, event_id: int) -> Optional[Dict]:
        return await database.get_event(event_id)

    async def _update_event(self, event_id: int, **kwargs) -> Optional[Dict]:
        return await database.update_event(event_id, **kwargs)

    async def _delete_event(self, event_id: int) -> bool:
        return await database.delete_event(event_id)

    async def _check_conflicts(self, start_time: str, end_time: str = None) -> Dict:
        """Check if the proposed time slot conflicts with existing events."""
        all_events = await database.list_events()
        conflicts = []
        for event in all_events:
            ev_start = event.get("start_time", "")
            ev_end = event.get("end_time", "")
            # Simple overlap check
            if ev_start and start_time:
                if end_time and ev_end:
                    if start_time < ev_end and end_time > ev_start:
                        conflicts.append(event)
                elif start_time == ev_start:
                    conflicts.append(event)
        return {"has_conflicts": len(conflicts) > 0, "conflicts": conflicts}

    async def process(self, request: Dict) -> Dict:
        """Process a calendar-related request."""
        action = request.get("action", "")
        params = request.get("params", {})

        action_map = {
            "create": "create_event",
            "create_event": "create_event",
            "schedule": "create_event",
            "list": "list_events",
            "list_events": "list_events",
            "get": "get_event",
            "get_event": "get_event",
            "update": "update_event",
            "update_event": "update_event",
            "reschedule": "update_event",
            "delete": "delete_event",
            "delete_event": "delete_event",
            "cancel": "delete_event",
            "check_conflicts": "check_conflicts",
        }

        tool_name = action_map.get(action)
        if not tool_name:
            return {
                "success": False,
                "error": f"Unknown calendar action: {action}",
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
