# AgentFlow — Multi-Agent AI System

A production-ready multi-agent AI system that helps users manage tasks, schedules, and information by coordinating specialized sub-agents and integrating multiple tools via MCP (Model Context Protocol).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Web Dashboard                       │
│            (HTML/CSS/JS + Chat UI)                   │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────┐
│              FastAPI Server (main.py)                │
│           /api/chat  /api/tasks  /api/events ...     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           Orchestrator Agent                         │
│     (Intent Classification + Request Routing)        │
├──────────┬──────────┬──────────┬────────────────────┤
│  Task    │ Calendar │  Notes   │    Workflow         │
│  Agent   │  Agent   │  Agent   │     Agent           │
└────┬─────┴────┬─────┴────┬─────┴────────┬───────────┘
     │          │          │              │
┌────▼──────────▼──────────▼──────────────▼───────────┐
│              MCP Tool Servers                        │
│   task_server  calendar_server  notes_server         │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              SQLite Database                         │
│    tasks | events | notes | workflows | agent_logs   │
└─────────────────────────────────────────────────────┘
```

## ✨ Features

### Multi-Agent Orchestration
- **Orchestrator Agent** — Primary coordinator with NLP intent classification
- **Task Agent** — CRUD operations for task management with priority/status tracking
- **Calendar Agent** — Event scheduling with automatic conflict detection
- **Notes Agent** — Knowledge management with search and categorization
- **Workflow Agent** — Multi-step workflow execution with pre-built templates

### MCP Tool Integration
- Three dedicated MCP servers (task, calendar, notes)
- Each server exposes tools following the Model Context Protocol
- Standardized tool schemas with input validation

### Built-in Workflow Templates
| Template | Description | Steps |
|----------|-------------|-------|
| Daily Standup Prep | Review in-progress and completed tasks + today's events | 3 |
| Project Setup | Create project notes, kickoff task, and meeting | 3 |
| Weekly Review | Review all tasks, events, and notes | 4 |
| Meeting Preparation | Create agenda, review tasks, find related notes | 3 |

### Premium Web Dashboard
- Natural language chat interface to interact with all agents
- Task board with filtering by status and priority
- Calendar event management
- Notes with search, categorization, and pinning
- Workflow visualization and execution
- Agent capability viewer with activity logs
- Dark mode with glassmorphism design

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Installation

```bash
cd hackathon
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

Then open **http://localhost:8080/dashboard** in your browser.

## 📡 API Endpoints

### Chat (Natural Language)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send natural language message to agents |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks (filter by `status`, `priority`) |
| POST | `/api/tasks` | Create a new task |
| GET | `/api/tasks/{id}` | Get task details |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| POST | `/api/tasks/{id}/complete` | Mark task as completed |

### Calendar
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events` | List events (filter by date range) |
| POST | `/api/events` | Create a new event |
| GET | `/api/events/{id}` | Get event details |
| PUT | `/api/events/{id}` | Update an event |
| DELETE | `/api/events/{id}` | Delete an event |

### Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes` | List notes (filter by `category`, `search`) |
| POST | `/api/notes` | Create a new note |
| GET | `/api/notes/{id}` | Get note details |
| PUT | `/api/notes/{id}` | Update a note |
| DELETE | `/api/notes/{id}` | Delete a note |
| GET | `/api/notes/search/{query}` | Search notes |

### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows` | List workflows |
| POST | `/api/workflows` | Create a workflow |
| GET | `/api/workflows/{id}` | Get workflow details |
| POST | `/api/workflows/{id}/execute` | Execute a workflow |
| GET | `/api/workflows/templates/list` | List workflow templates |
| POST | `/api/workflows/from-template` | Create from template |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System status and data summary |
| GET | `/api/agents` | List agent capabilities |
| GET | `/api/logs` | Agent activity logs |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python, FastAPI, Uvicorn |
| Database | SQLite (via aiosqlite) |
| MCP Servers | MCP Python SDK |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Styling | Custom CSS with CSS Variables |

## 📁 Project Structure

```
hackathon/
├── main.py                    # FastAPI server & API routes
├── database.py                # SQLite database operations
├── requirements.txt           # Python dependencies
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base agent class
│   ├── orchestrator.py        # Primary orchestrator agent
│   ├── task_agent.py          # Task management agent
│   ├── calendar_agent.py      # Calendar/scheduling agent
│   ├── notes_agent.py         # Notes management agent
│   └── workflow_agent.py      # Multi-step workflow agent
├── mcp_servers/
│   ├── __init__.py
│   ├── task_server.py         # MCP task tool server
│   ├── calendar_server.py     # MCP calendar tool server
│   └── notes_server.py        # MCP notes tool server
└── static/
    ├── index.html             # Dashboard HTML
    ├── styles.css             # Premium dark theme CSS
    └── app.js                 # Dashboard JavaScript
```
