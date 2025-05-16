"""
Database management for GeminiTask.
Handles SQLite interactions for tasks, contexts, and projects.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
import json

# Database setup
DB_DIR = Path.home() / ".geminitask"
DB_FILE = DB_DIR / "geminitask.db"


def ensure_db_dir():
    """Ensure the database directory exists."""
    DB_DIR.mkdir(exist_ok=True)


def get_db_connection():
    """Get a connection to the SQLite database."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_db():
    """Initialize the database with the required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create contexts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contexts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Create projects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        priority TEXT,
        due_date_time TEXT,
        context_id INTEGER,
        project_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed BOOLEAN DEFAULT 0,
        FOREIGN KEY (context_id) REFERENCES contexts(id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    ''')
    
    conn.commit()
    conn.close()


# Context management functions
def add_context(name):
    """Add a new context."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO contexts (name) VALUES (?)", (name,))
        conn.commit()
        context_id = cursor.lastrowid
        return {"success": True, "id": context_id, "name": name}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"Context '{name}' already exists"}
    finally:
        conn.close()


def get_context_by_name(name):
    """Get a context by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contexts WHERE name = ?", (name,))
    context = cursor.fetchone()
    
    conn.close()
    
    if context:
        return dict(context)
    return None


def list_contexts():
    """List all contexts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contexts ORDER BY name")
    contexts = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return contexts


# Project management functions
def add_project(name):
    """Add a new project."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        conn.commit()
        project_id = cursor.lastrowid
        return {"success": True, "id": project_id, "name": name}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"Project '{name}' already exists"}
    finally:
        conn.close()


def get_project_by_name(name):
    """Get a project by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
    project = cursor.fetchone()
    
    conn.close()
    
    if project:
        return dict(project)
    return None


def list_projects():
    """List all projects."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects ORDER BY name")
    projects = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return projects


# Task management functions
def add_task(description, priority=None, due_date_time=None, context_name=None, project_name=None):
    """Add a new task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    context_id = None
    if context_name:
        context = get_context_by_name(context_name)
        if context:
            context_id = context["id"]
        else:
            # Automatically create the context if it doesn't exist
            result = add_context(context_name)
            if result["success"]:
                context_id = result["id"]
    
    project_id = None
    if project_name:
        project = get_project_by_name(project_name)
        if project:
            project_id = project["id"]
        else:
            # Automatically create the project if it doesn't exist
            result = add_project(project_name)
            if result["success"]:
                project_id = result["id"]
    
    try:
        cursor.execute(
            """
            INSERT INTO tasks 
            (description, priority, due_date_time, context_id, project_id) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (description, priority, due_date_time, context_id, project_id)
        )
        conn.commit()
        task_id = cursor.lastrowid
        
        # Fetch the newly created task
        cursor.execute(
            """
            SELECT t.*, c.name as context_name, p.name as project_name
            FROM tasks t
            LEFT JOIN contexts c ON t.context_id = c.id
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.id = ?
            """,
            (task_id,)
        )
        task = cursor.fetchone()
        
        return {"success": True, "task": dict(task) if task else None}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def list_tasks(
    all_tasks=False, 
    priority=None, 
    due_range=None, 
    context_name=None, 
    project_name=None, 
    overdue=False, 
    completed=False
):
    """List tasks based on filters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT t.*, c.name as context_name, p.name as project_name
    FROM tasks t
    LEFT JOIN contexts c ON t.context_id = c.id
    LEFT JOIN projects p ON t.project_id = p.id
    WHERE 1=1
    """
    params = []
    
    # Apply filters
    if not all_tasks and not completed:
        query += " AND t.completed = 0"
    
    if completed:
        query += " AND t.completed = 1"
    
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    
    if due_range:
        # due_range should be a tuple of (start_date, end_date) in ISO format
        query += " AND t.due_date_time BETWEEN ? AND ?"
        params.extend(due_range)
    
    if context_name:
        query += " AND c.name = ?"
        params.append(context_name)
    
    if project_name:
        query += " AND p.name = ?"
        params.append(project_name)
    
    if overdue:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query += " AND t.due_date_time < ? AND t.completed = 0"
        params.append(now)
    
    query += " ORDER BY t.due_date_time ASC, t.priority DESC, t.id ASC"
    
    cursor.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return tasks


def get_task(task_id):
    """Get a task by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT t.*, c.name as context_name, p.name as project_name
        FROM tasks t
        LEFT JOIN contexts c ON t.context_id = c.id
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.id = ?
        """,
        (task_id,)
    )
    task = cursor.fetchone()
    
    conn.close()
    
    if task:
        return dict(task)
    return None


def mark_task_done(task_id):
    """Mark a task as completed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?",
            (task_id,)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            return {"success": True}
        else:
            return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def edit_task(task_id, description=None, priority=None, due_date_time=None, context_name=None, project_name=None):
    """Edit an existing task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the current task
    current_task = get_task(task_id)
    if not current_task:
        return {"success": False, "error": f"Task with ID {task_id} not found"}
    
    # Prepare updates
    updates = []
    params = []
    
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if priority is not None:
        updates.append("priority = ?")
        params.append(priority)
    
    if due_date_time is not None:
        updates.append("due_date_time = ?")
        params.append(due_date_time)
    
    context_id = current_task.get("context_id")
    if context_name is not None:
        if context_name:
            context = get_context_by_name(context_name)
            if not context:
                # Create the context if it doesn't exist
                result = add_context(context_name)
                if result["success"]:
                    context_id = result["id"]
                else:
                    return result
            else:
                context_id = context["id"]
        else:
            context_id = None
        
        updates.append("context_id = ?")
        params.append(context_id)
    
    project_id = current_task.get("project_id")
    if project_name is not None:
        if project_name:
            project = get_project_by_name(project_name)
            if not project:
                # Create the project if it doesn't exist
                result = add_project(project_name)
                if result["success"]:
                    project_id = result["id"]
                else:
                    return result
            else:
                project_id = project["id"]
        else:
            project_id = None
        
        updates.append("project_id = ?")
        params.append(project_id)
    
    if not updates:
        return {"success": False, "error": "No updates provided"}
    
    try:
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            # Get the updated task
            updated_task = get_task(task_id)
            return {"success": True, "task": updated_task}
        else:
            return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def delete_task(task_id):
    """Delete a task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {"success": True}
        else:
            return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


# Initialize the database when the module is imported
init_db()
