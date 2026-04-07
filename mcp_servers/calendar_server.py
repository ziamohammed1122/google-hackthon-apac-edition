"""
MCP Calendar Server — Exposes calendar/scheduling tools via MCP protocol.
Tools: create_event, list_events, update_event, delete_event, get_event
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import database

app = Server("calendar-manager")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_event",
            description="Create a new calendar event with title, start_time, end_time, description, location, and attendees",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                    "end_time": {"type": "string", "description": "End time in ISO format"},
                    "description": {"type": "string", "description": "Event description"},
                    "location": {"type": "string", "description": "Event location"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendees"}
                },
                "required": ["title", "start_time"]
            }
        ),
        Tool(
            name="list_events",
            description="List calendar events, optionally filtered by date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_after": {"type": "string", "description": "Show events starting after this date (ISO format)"},
                    "start_before": {"type": "string", "description": "Show events starting before this date (ISO format)"}
                }
            }
        ),
        Tool(
            name="get_event",
            description="Get a specific event by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "integer", "description": "The event ID"}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="update_event",
            description="Update an event's details",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "integer", "description": "The event ID to update"},
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "attendees": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="delete_event",
            description="Delete a calendar event by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "integer", "description": "The event ID to delete"}
                },
                "required": ["event_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "create_event":
            result = await database.create_event(
                title=arguments["title"],
                start_time=arguments["start_time"],
                end_time=arguments.get("end_time"),
                description=arguments.get("description", ""),
                location=arguments.get("location", ""),
                attendees=arguments.get("attendees")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_events":
            result = await database.list_events(
                start_after=arguments.get("start_after"),
                start_before=arguments.get("start_before")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_event":
            result = await database.get_event(arguments["event_id"])
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Event not found")]

        elif name == "update_event":
            event_id = arguments.pop("event_id")
            result = await database.update_event(event_id, **arguments)
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Event not found")]

        elif name == "delete_event":
            await database.delete_event(arguments["event_id"])
            return [TextContent(type="text", text=f"Event {arguments['event_id']} deleted successfully")]

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
