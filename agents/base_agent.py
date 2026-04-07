"""
Base Agent — Abstract base class for all agents in the system.
Provides common interface for tool execution, logging, and communication.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import database


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: Dict[str, callable] = {}
        self.execution_log: List[Dict] = []

    def register_tool(self, name: str, func: callable, description: str = ""):
        """Register a tool that this agent can use."""
        self.tools[name] = {
            "func": func,
            "description": description
        }

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool and log the action."""
        if tool_name not in self.tools:
            error = f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
            await self._log_action(tool_name, kwargs, {"error": error}, "error")
            return {"error": error}

        try:
            result = await self.tools[tool_name]["func"](**kwargs)
            await self._log_action(tool_name, kwargs, result, "success")
            return result
        except Exception as e:
            error_result = {"error": str(e)}
            await self._log_action(tool_name, kwargs, error_result, "error")
            return error_result

    async def _log_action(self, action: str, input_data: Any, output_data: Any, status: str):
        """Log an agent action to the database."""
        log_entry = {
            "agent": self.name,
            "action": action,
            "input": input_data,
            "output": output_data,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.execution_log.append(log_entry)
        try:
            await database.log_agent_action(
                agent_name=self.name,
                action=action,
                input_data=input_data,
                output_data=output_data if not isinstance(output_data, str) else {"result": output_data},
                status=status
            )
        except Exception:
            pass  # Don't fail if logging fails

    @abstractmethod
    async def process(self, request: Dict) -> Dict:
        """Process an incoming request. Must be implemented by subclasses."""
        pass

    def get_capabilities(self) -> Dict:
        """Return this agent's capabilities."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": {k: v["description"] for k, v in self.tools.items()}
        }
