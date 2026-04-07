"""
Multi-Agent AI System — FastAPI Server
Main entry point for the API-based multi-agent system.
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import database
from agents.orchestrator import OrchestratorAgent


# ─── Pydantic Models ──────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str = Field(..., description="Natural language message to the agent system")

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None

class EventCreate(BaseModel):
    title: str
    start_time: str
    end_time: Optional[str] = None
    description: str = ""
    location: str = ""
    attendees: Optional[List[str]] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class NoteCreate(BaseModel):
    title: str
    content: str = ""
    tags: Optional[List[str]] = None
    category: str = "general"

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    pinned: Optional[bool] = None

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    steps: Optional[List[Dict[str, Any]]] = None

class WorkflowFromTemplate(BaseModel):
    template_name: str
    overrides: Optional[Dict[str, Any]] = None


# ─── Application Setup ────────────────────────────────────────

orchestrator: Optional[OrchestratorAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and orchestrator on startup."""
    global orchestrator
    await database.init_db()
    orchestrator = OrchestratorAgent()
    print("🤖 Multi-Agent AI System initialized")
    print("📊 Database ready")
    print("🔧 Agents: TaskAgent, CalendarAgent, NotesAgent, WorkflowAgent")
    print("🌐 API server running at http://localhost:8080")
    print("🖥️  Dashboard at http://localhost:8080/dashboard")
    yield
    print("👋 Shutting down Multi-Agent AI System")

app = FastAPI(
    title="Multi-Agent AI System",
    description="A multi-agent system for task management, scheduling, and information organization",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Dashboard Route ──────────────────────────────────────────

@app.get("/dashboard")
async def dashboard():
    """Serve the web dashboard."""
    return FileResponse("static/index.html")


# ─── Chat / NLP Endpoint ──────────────────────────────────────

@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """Natural language interface to the agent system."""
    result = await orchestrator.process({"message": msg.message})
    return result


# ─── System Status ─────────────────────────────────────────────

@app.get("/api/status")
async def system_status():
    """Get system status and data summary."""
    return await orchestrator.process({"action": "status"})


@app.get("/api/logs")
async def agent_logs(agent_name: Optional[str] = None, limit: int = 50):
    """Get recent agent activity logs."""
    return await orchestrator.process({"action": "logs", "params": {"agent_name": agent_name, "limit": limit}})


# ─── Task API ──────────────────────────────────────────────────

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    """Create a new task."""
    result = await orchestrator.process({
        "agent": "task", "action": "create",
        "params": task.model_dump(exclude_none=True)
    })
    return result

@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None, priority: Optional[str] = None):
    """List tasks with optional filters."""
    params = {}
    if status: params["status"] = status
    if priority: params["priority"] = priority
    result = await orchestrator.process({"agent": "task", "action": "list", "params": params})
    return result

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a specific task."""
    result = await orchestrator.process({"agent": "task", "action": "get", "params": {"task_id": task_id}})
    return result

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    """Update a task."""
    params = task.model_dump(exclude_none=True)
    params["task_id"] = task_id
    result = await orchestrator.process({"agent": "task", "action": "update", "params": params})
    return result

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task."""
    result = await orchestrator.process({"agent": "task", "action": "delete", "params": {"task_id": task_id}})
    return result

@app.post("/api/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    """Mark a task as completed."""
    result = await orchestrator.process({"agent": "task", "action": "complete", "params": {"task_id": task_id}})
    return result


# ─── Calendar API ──────────────────────────────────────────────

@app.post("/api/events")
async def create_event(event: EventCreate):
    """Create a new calendar event."""
    result = await orchestrator.process({
        "agent": "calendar", "action": "create",
        "params": event.model_dump(exclude_none=True)
    })
    return result

@app.get("/api/events")
async def list_events(start_after: Optional[str] = None, start_before: Optional[str] = None):
    """List events with optional date range."""
    params = {}
    if start_after: params["start_after"] = start_after
    if start_before: params["start_before"] = start_before
    result = await orchestrator.process({"agent": "calendar", "action": "list", "params": params})
    return result

@app.get("/api/events/{event_id}")
async def get_event(event_id: int):
    """Get a specific event."""
    result = await orchestrator.process({"agent": "calendar", "action": "get", "params": {"event_id": event_id}})
    return result

@app.put("/api/events/{event_id}")
async def update_event(event_id: int, event: EventUpdate):
    """Update an event."""
    params = event.model_dump(exclude_none=True)
    params["event_id"] = event_id
    result = await orchestrator.process({"agent": "calendar", "action": "update", "params": params})
    return result

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: int):
    """Delete an event."""
    result = await orchestrator.process({"agent": "calendar", "action": "delete", "params": {"event_id": event_id}})
    return result


# ─── Notes API ─────────────────────────────────────────────────

@app.post("/api/notes")
async def create_note(note: NoteCreate):
    """Create a new note."""
    result = await orchestrator.process({
        "agent": "notes", "action": "create",
        "params": note.model_dump(exclude_none=True)
    })
    return result

@app.get("/api/notes")
async def list_notes(category: Optional[str] = None, search: Optional[str] = None):
    """List notes with optional filters."""
    params = {}
    if category: params["category"] = category
    if search: params["search"] = search
    result = await orchestrator.process({"agent": "notes", "action": "list", "params": params})
    return result

@app.get("/api/notes/{note_id}")
async def get_note(note_id: int):
    """Get a specific note."""
    result = await orchestrator.process({"agent": "notes", "action": "get", "params": {"note_id": note_id}})
    return result

@app.put("/api/notes/{note_id}")
async def update_note(note_id: int, note: NoteUpdate):
    """Update a note."""
    params = note.model_dump(exclude_none=True)
    params["note_id"] = note_id
    result = await orchestrator.process({"agent": "notes", "action": "update", "params": params})
    return result

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note."""
    result = await orchestrator.process({"agent": "notes", "action": "delete", "params": {"note_id": note_id}})
    return result

@app.get("/api/notes/search/{query}")
async def search_notes(query: str):
    """Search notes by keyword."""
    result = await orchestrator.process({"agent": "notes", "action": "search", "params": {"query": query}})
    return result


# ─── Workflow API ──────────────────────────────────────────────

@app.post("/api/workflows")
async def create_workflow(wf: WorkflowCreate):
    """Create a new workflow."""
    result = await orchestrator.process({
        "agent": "workflow", "action": "create",
        "params": wf.model_dump(exclude_none=True)
    })
    return result

@app.get("/api/workflows")
async def list_workflows(status: Optional[str] = None):
    """List all workflows."""
    params = {}
    if status: params["status"] = status
    result = await orchestrator.process({"agent": "workflow", "action": "list", "params": params})
    return result

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: int):
    """Get a specific workflow."""
    result = await orchestrator.process({"agent": "workflow", "action": "get", "params": {"workflow_id": workflow_id}})
    return result

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: int):
    """Execute a workflow."""
    result = await orchestrator.process({"agent": "workflow", "action": "execute", "params": {"workflow_id": workflow_id}})
    return result

@app.get("/api/workflows/templates/list")
async def list_workflow_templates():
    """List available workflow templates."""
    result = await orchestrator.process({"agent": "workflow", "action": "templates", "params": {}})
    return result

@app.post("/api/workflows/from-template")
async def create_workflow_from_template(req: WorkflowFromTemplate):
    """Create a workflow from a template."""
    result = await orchestrator.process({
        "agent": "workflow", "action": "create_from_template",
        "params": req.model_dump(exclude_none=True)
    })
    return result


# ─── Agent Capabilities ───────────────────────────────────────

@app.get("/api/agents")
async def list_agents():
    """List all available agents and their capabilities."""
    agents = {}
    for name, agent in orchestrator.agent_registry.items():
        agents[name] = agent.get_capabilities()
    return {"agents": agents}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
