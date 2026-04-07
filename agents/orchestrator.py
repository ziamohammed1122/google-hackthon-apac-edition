"""
Orchestrator Agent — Primary coordinating agent.
Routes requests to appropriate sub-agents, handles intent classification,
and manages complex multi-agent interactions.
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from .base_agent import BaseAgent
from .task_agent import TaskAgent
from .calendar_agent import CalendarAgent
from .notes_agent import NotesAgent
from .workflow_agent import WorkflowAgent
import database


class OrchestratorAgent(BaseAgent):
    """
    Primary orchestrator that classifies user intent and delegates
    to the appropriate sub-agent(s).
    """

    # Intent classification keywords
    INTENT_PATTERNS = {
        "task": {
            "keywords": ["task", "todo", "to-do", "to do", "assign", "deadline", "priority",
                         "complete", "finish", "done", "progress", "backlog"],
            "create": ["create task", "add task", "new task", "make task", "add a task", "create a task"],
            "list": ["list task", "show task", "my task", "all task", "pending task", "view task"],
            "update": ["update task", "change task", "modify task", "edit task"],
            "delete": ["delete task", "remove task", "cancel task"],
            "complete": ["complete task", "finish task", "mark done", "mark complete", "task done"],
        },
        "calendar": {
            "keywords": ["event", "meeting", "schedule", "calendar", "appointment", "book",
                         "reschedule", "invite", "attend", "when", "time slot"],
            "create": ["create event", "schedule", "book", "add event", "new meeting", "set up meeting",
                        "create meeting", "add meeting", "schedule meeting"],
            "list": ["list event", "show event", "my event", "upcoming", "calendar", "what's on",
                      "show schedule", "my schedule", "today's event"],
            "update": ["update event", "reschedule", "change event", "modify event", "move meeting"],
            "delete": ["delete event", "cancel event", "remove event", "cancel meeting"],
            "check_conflicts": ["conflict", "available", "free slot", "busy"],
        },
        "notes": {
            "keywords": ["note", "write down", "remember", "jot", "memo", "document",
                         "record", "save info", "knowledge"],
            "create": ["create note", "add note", "new note", "write note", "jot down", "make note",
                        "take note", "save note"],
            "list": ["list note", "show note", "my note", "all note", "view note"],
            "search": ["search note", "find note", "look up", "search for"],
            "update": ["update note", "edit note", "modify note", "change note"],
            "delete": ["delete note", "remove note"],
            "pin": ["pin note", "unpin note", "pin"],
        },
        "workflow": {
            "keywords": ["workflow", "automate", "pipeline", "sequence", "multi-step",
                         "standup", "review", "prep", "prepare"],
            "create": ["create workflow", "new workflow", "build workflow"],
            "execute": ["run workflow", "execute workflow", "start workflow"],
            "list": ["list workflow", "show workflow", "my workflow"],
            "templates": ["template", "workflow template", "available workflow"],
            "create_from_template": ["from template", "use template"],
        }
    }

    def __init__(self):
        super().__init__(
            name="OrchestratorAgent",
            description="Primary coordinating agent that routes requests to specialized sub-agents."
        )

        # Initialize sub-agents
        self.task_agent = TaskAgent()
        self.calendar_agent = CalendarAgent()
        self.notes_agent = NotesAgent()

        # Agent registry for workflow agent
        self.agent_registry = {
            "task": self.task_agent,
            "calendar": self.calendar_agent,
            "notes": self.notes_agent,
        }
        self.workflow_agent = WorkflowAgent(agent_registry=self.agent_registry)
        self.agent_registry["workflow"] = self.workflow_agent

        # Register orchestrator tools
        self._register_tools()

    def _register_tools(self):
        self.register_tool("route_request", self._route_request, "Route request to appropriate agent")
        self.register_tool("get_system_status", self._get_system_status, "Get system status and capabilities")
        self.register_tool("get_agent_logs", self._get_agent_logs, "Get recent agent activity logs")

    def _classify_intent(self, message: str) -> Dict:
        """Classify the user's intent from a natural language message."""
        message_lower = message.lower().strip()

        best_agent = None
        best_action = None
        best_score = 0

        for agent_type, patterns in self.INTENT_PATTERNS.items():
            # Check keywords
            keyword_matches = sum(1 for kw in patterns["keywords"] if kw in message_lower)

            if keyword_matches == 0:
                continue

            # Check action patterns
            for action, action_patterns in patterns.items():
                if action == "keywords":
                    continue
                for pattern in action_patterns:
                    if pattern in message_lower:
                        score = keyword_matches + len(pattern)
                        if score > best_score:
                            best_score = score
                            best_agent = agent_type
                            best_action = action

            # If keywords matched but no specific action, default to list
            if keyword_matches > 0 and (best_agent != agent_type or best_action is None):
                if keyword_matches > best_score:
                    best_agent = agent_type
                    best_action = "list"
                    best_score = keyword_matches

        return {
            "agent": best_agent,
            "action": best_action,
            "confidence": min(best_score / 10, 1.0) if best_score > 0 else 0
        }

    def _extract_params(self, message: str, agent_type: str, action: str) -> Dict:
        """Extract parameters from the user's message based on intent."""
        params = {}
        message_lower = message.lower()

        if agent_type == "task":
            # Extract title from message
            title_patterns = [
                r"(?:create|add|new|make)\s+(?:a\s+)?task\s+(?:called|named|titled)?\s*[\"']?(.+?)[\"']?\s*$",
                r"(?:create|add|new|make)\s+(?:a\s+)?task\s*:\s*(.+)",
                r"task\s*:\s*(.+)",
            ]
            for pattern in title_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    params["title"] = match.group(1).strip()
                    break

            # Extract priority
            for p in ["critical", "high", "medium", "low"]:
                if p in message_lower:
                    params["priority"] = p
                    break

            # Extract status for list/update
            for s in ["pending", "in_progress", "completed", "cancelled"]:
                if s.replace("_", " ") in message_lower or s in message_lower:
                    params["status"] = s
                    break

            # Extract task_id
            id_match = re.search(r"(?:task\s*#?|id\s*:?\s*)(\d+)", message, re.IGNORECASE)
            if id_match:
                params["task_id"] = int(id_match.group(1))

        elif agent_type == "calendar":
            # Extract event title
            title_patterns = [
                r"(?:schedule|create|book|add)\s+(?:a\s+)?(?:meeting|event)\s+(?:called|named|titled|for)?\s*[\"']?(.+?)[\"']?\s*(?:on|at|from|$)",
                r"(?:meeting|event)\s*:\s*(.+?)(?:on|at|from|$)",
            ]
            for pattern in title_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    params["title"] = match.group(1).strip()
                    break

            # Extract event_id
            id_match = re.search(r"(?:event\s*#?|id\s*:?\s*)(\d+)", message, re.IGNORECASE)
            if id_match:
                params["event_id"] = int(id_match.group(1))

        elif agent_type == "notes":
            # Extract note title
            title_patterns = [
                r"(?:create|add|new|write|make|take|save)\s+(?:a\s+)?note\s+(?:called|named|titled|about)?\s*[\"']?(.+?)[\"']?\s*$",
                r"note\s*:\s*(.+)",
            ]
            for pattern in title_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    params["title"] = match.group(1).strip()
                    break

            # Extract search query
            search_match = re.search(r"(?:search|find|look up)\s+(?:notes?\s+)?(?:for|about)?\s*[\"']?(.+?)[\"']?\s*$",
                                     message, re.IGNORECASE)
            if search_match:
                params["query"] = search_match.group(1).strip()

            # Extract note_id
            id_match = re.search(r"(?:note\s*#?|id\s*:?\s*)(\d+)", message, re.IGNORECASE)
            if id_match:
                params["note_id"] = int(id_match.group(1))

            # Extract category
            for cat in ["meeting", "project", "idea", "reference", "general"]:
                if cat in message_lower:
                    params["category"] = cat
                    break

        elif agent_type == "workflow":
            # Extract template name
            for template in ["daily_standup", "project_setup", "weekly_review", "meeting_prep"]:
                if template.replace("_", " ") in message_lower:
                    params["template_name"] = template
                    break

            # Extract workflow_id
            id_match = re.search(r"(?:workflow\s*#?|id\s*:?\s*)(\d+)", message, re.IGNORECASE)
            if id_match:
                params["workflow_id"] = int(id_match.group(1))

        return params

    async def _route_request(self, message: str) -> Dict:
        """Route a natural language request to the appropriate agent."""
        intent = self._classify_intent(message)

        if not intent["agent"]:
            return {
                "success": False,
                "message": "I couldn't determine what you'd like to do. Try specifying a task, event, note, or workflow action.",
                "suggestions": [
                    "Create a task: 'Create a task called Review PR'",
                    "Schedule event: 'Schedule a meeting for tomorrow at 2pm'",
                    "Create note: 'Create a note about project requirements'",
                    "Run workflow: 'Run daily standup workflow'",
                    "List items: 'Show my tasks' / 'Show my events' / 'Show my notes'",
                ]
            }

        params = self._extract_params(message, intent["agent"], intent["action"])
        agent = self.agent_registry.get(intent["agent"])

        if not agent:
            return {"success": False, "error": f"Agent '{intent['agent']}' not available"}

        result = await agent.process({"action": intent["action"], "params": params})

        return {
            "success": True,
            "intent": intent,
            "extracted_params": params,
            "result": result,
            "agent_used": intent["agent"],
            "action_taken": intent["action"]
        }

    async def _get_system_status(self) -> Dict:
        """Get the current system status including all agent capabilities."""
        agents = {}
        for name, agent in self.agent_registry.items():
            agents[name] = agent.get_capabilities()

        # Get counts
        tasks = await database.list_tasks()
        events = await database.list_events()
        notes = await database.list_notes()
        workflows = await database.list_workflows()

        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": agents,
            "data_summary": {
                "total_tasks": len(tasks),
                "pending_tasks": sum(1 for t in tasks if t.get("status") == "pending"),
                "in_progress_tasks": sum(1 for t in tasks if t.get("status") == "in_progress"),
                "completed_tasks": sum(1 for t in tasks if t.get("status") == "completed"),
                "total_events": len(events),
                "total_notes": len(notes),
                "total_workflows": len(workflows),
            }
        }

    async def _get_agent_logs(self, agent_name: str = None, limit: int = 20) -> list:
        """Get recent agent activity logs."""
        return await database.get_agent_logs(agent_name, limit)

    async def process(self, request: Dict) -> Dict:
        """Process an incoming request — either structured or natural language."""
        # If it's a natural language message, classify and route
        if "message" in request:
            return await self._route_request(request["message"])

        # If it's a structured request, route directly
        agent_name = request.get("agent")
        action = request.get("action")
        params = request.get("params", {})

        if agent_name and agent_name in self.agent_registry:
            agent = self.agent_registry[agent_name]
            return await agent.process({"action": action, "params": params})

        # Handle orchestrator-level actions
        if action == "status":
            return await self._get_system_status()
        elif action == "logs":
            logs = await self._get_agent_logs(**params)
            return {"success": True, "data": logs}

        return {"success": False, "error": "Invalid request format"}
