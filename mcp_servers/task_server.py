"""
MCP Task Server — Exposes task management tools via MCP protocol.
Tools: create_task, list_tasks, update_task, delete_task, get_task
"""

import json
import sys
import os

# Add parent dir so we can import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import database

app = Server("task-manager")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_task",
            description="Create a new task with title, description, priority (low/medium/high/critical), due_date, and tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Task priority"},
                    "due_date": {"type": "string", "description": "Due date in ISO format (YYYY-MM-DD)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="list_tasks",
            description="List all tasks, optionally filtered by status or priority",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                }
            }
        ),
        Tool(
            name="get_task",
            description="Get a specific task by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="update_task",
            description="Update a task's title, description, status, priority, due_date, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to update"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "due_date": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="delete_task",
            description="Delete a task by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to delete"}
                },
                "required": ["task_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "create_task":
            result = await database.create_task(
                title=arguments["title"],
                description=arguments.get("description", ""),
                priority=arguments.get("priority", "medium"),
                due_date=arguments.get("due_date"),
                tags=arguments.get("tags")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_tasks":
            result = await database.list_tasks(
                status=arguments.get("status"),
                priority=arguments.get("priority")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_task":
            result = await database.get_task(arguments["task_id"])
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Task not found")]

        elif name == "update_task":
            task_id = arguments.pop("task_id")
            result = await database.update_task(task_id, **arguments)
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Task not found")]

        elif name == "delete_task":
            await database.delete_task(arguments["task_id"])
            return [TextContent(type="text", text=f"Task {arguments['task_id']} deleted successfully")]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    await database.init_db()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
