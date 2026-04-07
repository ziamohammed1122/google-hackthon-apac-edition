"""
Workflow Agent — Sub-agent responsible for multi-step workflow execution.
Coordinates complex operations across multiple agents.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from .base_agent import BaseAgent
import database


class WorkflowAgent(BaseAgent):
    """Agent specialized in executing multi-step workflows."""

    WORKFLOW_TEMPLATES = {
        "daily_standup": {
            "name": "Daily Standup Prep",
            "description": "Prepare for daily standup by reviewing tasks and schedule",
            "steps": [
                {"agent": "task", "action": "list", "params": {"status": "in_progress"}, "label": "Get in-progress tasks"},
                {"agent": "task", "action": "list", "params": {"status": "completed"}, "label": "Get recently completed tasks"},
                {"agent": "calendar", "action": "list", "params": {}, "label": "Get today's events"},
            ]
        },
        "project_setup": {
            "name": "Project Setup",
            "description": "Set up a new project with tasks, events, and notes",
            "steps": [
                {"agent": "notes", "action": "create", "params": {"title": "Project Notes", "category": "project"}, "label": "Create project notes"},
                {"agent": "task", "action": "create", "params": {"title": "Project kickoff", "priority": "high"}, "label": "Create kickoff task"},
                {"agent": "calendar", "action": "create", "params": {"title": "Project Kickoff Meeting"}, "label": "Schedule kickoff meeting"},
            ]
        },
        "weekly_review": {
            "name": "Weekly Review",
            "description": "Review the week's progress and plan ahead",
            "steps": [
                {"agent": "task", "action": "list", "params": {"status": "completed"}, "label": "Review completed tasks"},
                {"agent": "task", "action": "list", "params": {"status": "pending"}, "label": "Review pending tasks"},
                {"agent": "calendar", "action": "list", "params": {}, "label": "Review upcoming events"},
                {"agent": "notes", "action": "list", "params": {}, "label": "Review recent notes"},
            ]
        },
        "meeting_prep": {
            "name": "Meeting Preparation",
            "description": "Prepare for an upcoming meeting",
            "steps": [
                {"agent": "notes", "action": "create", "params": {"title": "Meeting Agenda", "category": "meeting"}, "label": "Create meeting agenda"},
                {"agent": "task", "action": "list", "params": {}, "label": "Review related tasks"},
                {"agent": "notes", "action": "search", "params": {"query": "meeting"}, "label": "Find related notes"},
            ]
        }
    }

    def __init__(self, agent_registry: Dict = None):
        super().__init__(
            name="WorkflowAgent",
            description="Executes multi-step workflows by coordinating actions across multiple agents."
        )
        self.agent_registry = agent_registry or {}
        self._register_tools()

    def _register_tools(self):
        self.register_tool("create_workflow", self._create_workflow, "Create a new workflow")
        self.register_tool("execute_workflow", self._execute_workflow, "Execute a workflow by ID")
        self.register_tool("list_workflows", self._list_workflows, "List all workflows")
        self.register_tool("get_workflow", self._get_workflow, "Get workflow details")
        self.register_tool("list_templates", self._list_templates, "List available workflow templates")
        self.register_tool("create_from_template", self._create_from_template, "Create workflow from template")

    async def _create_workflow(self, name: str, description: str = "", steps: list = None) -> Dict:
        return await database.create_workflow(name, description, steps)

    async def _list_workflows(self, status: str = None) -> list:
        return await database.list_workflows(status)

    async def _get_workflow(self, workflow_id: int) -> Optional[Dict]:
        return await database.get_workflow(workflow_id)

    async def _list_templates(self) -> Dict:
        return {k: {"name": v["name"], "description": v["description"], "step_count": len(v["steps"])}
                for k, v in self.WORKFLOW_TEMPLATES.items()}

    async def _create_from_template(self, template_name: str, overrides: dict = None) -> Dict:
        if template_name not in self.WORKFLOW_TEMPLATES:
            return {"error": f"Template '{template_name}' not found"}

        template = self.WORKFLOW_TEMPLATES[template_name]
        steps = template["steps"].copy()

        # Apply any parameter overrides
        if overrides:
            for i, step in enumerate(steps):
                if str(i) in overrides:
                    step["params"].update(overrides[str(i)])

        return await database.create_workflow(
            name=template["name"],
            description=template["description"],
            steps=steps
        )

    async def _execute_workflow(self, workflow_id: int) -> Dict:
        """Execute a workflow step by step, delegating to appropriate agents."""
        workflow = await database.get_workflow(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}

        steps = json.loads(workflow["steps"]) if isinstance(workflow["steps"], str) else workflow["steps"]
        results = json.loads(workflow["results"]) if isinstance(workflow["results"], str) else workflow["results"]

        # Update status to running
        await database.update_workflow(workflow_id, status="running")

        step_results = []
        for i, step in enumerate(steps):
            agent_name = step.get("agent", "")
            action = step.get("action", "")
            params = step.get("params", {})
            label = step.get("label", f"Step {i+1}")

            # Find the appropriate agent
            agent = self.agent_registry.get(agent_name)
            if not agent:
                step_result = {
                    "step": i,
                    "label": label,
                    "status": "error",
                    "error": f"Agent '{agent_name}' not found in registry"
                }
            else:
                try:
                    result = await agent.process({"action": action, "params": params})
                    step_result = {
                        "step": i,
                        "label": label,
                        "status": "success",
                        "data": result
                    }
                except Exception as e:
                    step_result = {
                        "step": i,
                        "label": label,
                        "status": "error",
                        "error": str(e)
                    }

            step_results.append(step_result)
            # Update current step progress
            await database.update_workflow(
                workflow_id,
                current_step=i + 1,
                results={"step_results": step_results}
            )

        # Determine final status
        all_success = all(r["status"] == "success" for r in step_results)
        final_status = "completed" if all_success else "partial"

        await database.update_workflow(workflow_id, status=final_status)

        return {
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": final_status,
            "total_steps": len(steps),
            "completed_steps": sum(1 for r in step_results if r["status"] == "success"),
            "results": step_results
        }

    async def process(self, request: Dict) -> Dict:
        """Process a workflow-related request."""
        action = request.get("action", "")
        params = request.get("params", {})

        action_map = {
            "create": "create_workflow",
            "create_workflow": "create_workflow",
            "execute": "execute_workflow",
            "execute_workflow": "execute_workflow",
            "run": "execute_workflow",
            "list": "list_workflows",
            "list_workflows": "list_workflows",
            "get": "get_workflow",
            "get_workflow": "get_workflow",
            "templates": "list_templates",
            "list_templates": "list_templates",
            "create_from_template": "create_from_template",
            "from_template": "create_from_template",
        }

        tool_name = action_map.get(action)
        if not tool_name:
            return {
                "success": False,
                "error": f"Unknown workflow action: {action}",
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
