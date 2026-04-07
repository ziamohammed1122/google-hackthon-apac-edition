"""
MCP Notes Server — Exposes note-taking tools via MCP protocol.
Tools: create_note, list_notes, update_note, delete_note, search_notes, get_note
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import database

app = Server("notes-manager")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_note",
            description="Create a new note with title, content, tags, and category",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title"},
                    "content": {"type": "string", "description": "Note content (supports markdown)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                    "category": {"type": "string", "description": "Note category (e.g., general, meeting, idea, reference)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="list_notes",
            description="List all notes, optionally filtered by category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                    "search": {"type": "string", "description": "Search in title and content"}
                }
            }
        ),
        Tool(
            name="get_note",
            description="Get a specific note by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "The note ID"}
                },
                "required": ["note_id"]
            }
        ),
        Tool(
            name="update_note",
            description="Update a note's title, content, tags, category, or pinned status",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "The note ID to update"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "category": {"type": "string"},
                    "pinned": {"type": "boolean"}
                },
                "required": ["note_id"]
            }
        ),
        Tool(
            name="delete_note",
            description="Delete a note by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "The note ID to delete"}
                },
                "required": ["note_id"]
            }
        ),
        Tool(
            name="search_notes",
            description="Search notes by keyword in title and content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "create_note":
            result = await database.create_note(
                title=arguments["title"],
                content=arguments.get("content", ""),
                tags=arguments.get("tags"),
                category=arguments.get("category", "general")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_notes":
            result = await database.list_notes(
                category=arguments.get("category"),
                search=arguments.get("search")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_note":
            result = await database.get_note(arguments["note_id"])
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Note not found")]

        elif name == "update_note":
            note_id = arguments.pop("note_id")
            if "pinned" in arguments:
                arguments["pinned"] = 1 if arguments["pinned"] else 0
            result = await database.update_note(note_id, **arguments)
            if result:
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            return [TextContent(type="text", text="Note not found")]

        elif name == "delete_note":
            await database.delete_note(arguments["note_id"])
            return [TextContent(type="text", text=f"Note {arguments['note_id']} deleted successfully")]

        elif name == "search_notes":
            result = await database.search_notes(arguments["query"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

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
