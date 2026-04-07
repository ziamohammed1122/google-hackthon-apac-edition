"""
Database module — SQLite setup and operations via aiosqlite.
Manages tasks, events, notes, and workflow tables.
"""

import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "agent_system.db")


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database tables."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                tags TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT DEFAULT '',
                attendees TEXT DEFAULT '[]',
                recurrence TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                category TEXT DEFAULT 'general',
                pinned INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                steps TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                current_step INTEGER DEFAULT 0,
                results TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'success',
                timestamp TEXT DEFAULT (datetime('now'))
            );
        """)
        await db.commit()
    finally:
        await db.close()


# ─── Task Operations ───────────────────────────────────────────

async def create_task(title, description="", priority="medium", due_date=None, tags=None):
    db = await get_db()
    try:
        import json
        tags_json = json.dumps(tags or [])
        cursor = await db.execute(
            "INSERT INTO tasks (title, description, priority, due_date, tags) VALUES (?, ?, ?, ?, ?)",
            (title, description, priority, due_date, tags_json)
        )
        await db.commit()
        task_id = cursor.lastrowid
        return await get_task(task_id)
    finally:
        await db.close()


async def get_task(task_id):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def list_tasks(status=None, priority=None):
    db = await get_db()
    try:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY created_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def update_task(task_id, **kwargs):
    db = await get_db()
    try:
        import json
        allowed = {"title", "description", "status", "priority", "due_date", "tags"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])
        if not updates:
            return await get_task(task_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        await db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await get_task(task_id)
    finally:
        await db.close()


async def delete_task(task_id):
    db = await get_db()
    try:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        return True
    finally:
        await db.close()


# ─── Event Operations ──────────────────────────────────────────

async def create_event(title, start_time, end_time=None, description="", location="", attendees=None):
    db = await get_db()
    try:
        import json
        attendees_json = json.dumps(attendees or [])
        cursor = await db.execute(
            "INSERT INTO events (title, start_time, end_time, description, location, attendees) VALUES (?, ?, ?, ?, ?, ?)",
            (title, start_time, end_time, description, location, attendees_json)
        )
        await db.commit()
        event_id = cursor.lastrowid
        return await get_event(event_id)
    finally:
        await db.close()


async def get_event(event_id):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def list_events(start_after=None, start_before=None):
    db = await get_db()
    try:
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        if start_after:
            query += " AND start_time >= ?"
            params.append(start_after)
        if start_before:
            query += " AND start_time <= ?"
            params.append(start_before)
        query += " ORDER BY start_time ASC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def update_event(event_id, **kwargs):
    db = await get_db()
    try:
        import json
        allowed = {"title", "description", "start_time", "end_time", "location", "attendees"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if "attendees" in updates and isinstance(updates["attendees"], list):
            updates["attendees"] = json.dumps(updates["attendees"])
        if not updates:
            return await get_event(event_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [event_id]
        await db.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await get_event(event_id)
    finally:
        await db.close()


async def delete_event(event_id):
    db = await get_db()
    try:
        await db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        await db.commit()
        return True
    finally:
        await db.close()


# ─── Notes Operations ──────────────────────────────────────────

async def create_note(title, content="", tags=None, category="general"):
    db = await get_db()
    try:
        import json
        tags_json = json.dumps(tags or [])
        cursor = await db.execute(
            "INSERT INTO notes (title, content, tags, category) VALUES (?, ?, ?, ?)",
            (title, content, tags_json, category)
        )
        await db.commit()
        note_id = cursor.lastrowid
        return await get_note(note_id)
    finally:
        await db.close()


async def get_note(note_id):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def list_notes(category=None, search=None):
    db = await get_db()
    try:
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY pinned DESC, updated_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def update_note(note_id, **kwargs):
    db = await get_db()
    try:
        import json
        allowed = {"title", "content", "tags", "category", "pinned"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])
        if not updates:
            return await get_note(note_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [note_id]
        await db.execute(f"UPDATE notes SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await get_note(note_id)
    finally:
        await db.close()


async def delete_note(note_id):
    db = await get_db()
    try:
        await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()
        return True
    finally:
        await db.close()


async def search_notes(query_text):
    return await list_notes(search=query_text)


# ─── Workflow Operations ───────────────────────────────────────

async def create_workflow(name, description="", steps=None):
    db = await get_db()
    try:
        import json
        steps_json = json.dumps(steps or [])
        cursor = await db.execute(
            "INSERT INTO workflows (name, description, steps) VALUES (?, ?, ?)",
            (name, description, steps_json)
        )
        await db.commit()
        return await get_workflow(cursor.lastrowid)
    finally:
        await db.close()


async def get_workflow(workflow_id):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def update_workflow(workflow_id, **kwargs):
    db = await get_db()
    try:
        import json
        allowed = {"name", "description", "steps", "status", "current_step", "results"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if "steps" in updates and isinstance(updates["steps"], list):
            updates["steps"] = json.dumps(updates["steps"])
        if "results" in updates and isinstance(updates["results"], dict):
            updates["results"] = json.dumps(updates["results"])
        if not updates:
            return await get_workflow(workflow_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [workflow_id]
        await db.execute(f"UPDATE workflows SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await get_workflow(workflow_id)
    finally:
        await db.close()


async def list_workflows(status=None):
    db = await get_db()
    try:
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


# ─── Agent Logging ─────────────────────────────────────────────

async def log_agent_action(agent_name, action, input_data=None, output_data=None, status="success"):
    db = await get_db()
    try:
        import json
        await db.execute(
            "INSERT INTO agent_logs (agent_name, action, input_data, output_data, status) VALUES (?, ?, ?, ?, ?)",
            (agent_name, action,
             json.dumps(input_data or {}),
             json.dumps(output_data or {}),
             status)
        )
        await db.commit()
    finally:
        await db.close()


async def get_agent_logs(agent_name=None, limit=50):
    db = await get_db()
    try:
        query = "SELECT * FROM agent_logs WHERE 1=1"
        params = []
        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()
