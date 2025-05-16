#!/usr/bin/env python3
"""
GeminiTask - A command-line task manager enhanced with the Gemini API.

This is the main application module that implements the CLI interface using Click.
"""

import os
import sys
import click
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
import calendar

import database as db
import utils
from config import get_api_key, set_api_key, get_config_value, set_config_value


console = Console()


def validate_priority(ctx, param, value):
    """Validate priority value."""
    if value and value.lower() not in ['high', 'medium', 'low']:
        raise click.BadParameter("Priority must be 'high', 'medium', or 'low'")
    return value.lower() if value else None


def check_gemini_api_key():
    """Check if Gemini API key is set."""
    api_key = get_api_key()
    if not api_key:
        console.print("[yellow]Warning: Gemini API key not set. AI features will be unavailable.[/yellow]")
        console.print("[yellow]Set it with: geminitask config --api-key YOUR_API_KEY[/yellow]")
        return False
    return True


def format_table_output(tasks, use_rich=True):
    """Format task list as a table using rich or tabulate."""
    if not tasks:
        return "No tasks found."
    
    if use_rich:
        table = Table(show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("Description")
        table.add_column("Priority", style="bold")
        table.add_column("Due Date")
        table.add_column("Context")
        table.add_column("Project")
        table.add_column("Status")
        
        for task in tasks:
            priority_color = {
                "high": "red",
                "medium": "yellow",
                "low": "green"
            }.get(task.get("priority", "").lower(), "white")
            
            status = "[green]Completed[/green]" if task.get("completed") else "Pending"
            
            # Format the due date in a friendly way
            due_date = utils.format_relative_date(task.get("due_date_time"))
            
            table.add_row(
                str(task.get("id")),
                task.get("description"),
                f"[{priority_color}]{task.get('priority', 'none')}[/{priority_color}]",
                due_date,
                task.get("context_name", ""),
                task.get("project_name", ""),
                status
            )
        
        return table
    else:
        # Use tabulate for non-rich output
        headers = ["ID", "Description", "Priority", "Due Date", "Context", "Project", "Status"]
        rows = []
        
        for task in tasks:
            due_date = utils.format_relative_date(task.get("due_date_time"))
            status = "Completed" if task.get("completed") else "Pending"
            
            rows.append([
                task.get("id"),
                task.get("description"),
                task.get("priority", "none"),
                due_date,
                task.get("context_name", ""),
                task.get("project_name", ""),
                status
            ])
        
        return tabulate(rows, headers=headers, tablefmt="grid")


# Define the CLI group
@click.group()
def cli():
    """GeminiTask - A smart command-line task manager powered by the Gemini API."""
    pass


# Config command
@cli.command()
@click.option("--api-key", help="Set the Gemini API key")
@click.option("--default-priority", type=click.Choice(['high', 'medium', 'low'], case_sensitive=False), 
              help="Set the default priority for new tasks")
def config(api_key, default_priority):
    """Configure GeminiTask settings."""
    if api_key:
        set_api_key(api_key)
        console.print("[green]Gemini API key set successfully.[/green]")
    
    if default_priority:
        set_config_value("priority_default", default_priority.lower())
        console.print(f"[green]Default priority set to {default_priority}.[/green]")
    
    if not api_key and not default_priority:
        # Display current configuration
        api_key = get_api_key()
        masked_key = f"{api_key[:4]}..." if api_key and len(api_key) > 4 else "Not set"
        
        default_priority = get_config_value("priority_default", "medium")
        
        table = Table(show_header=True, title="GeminiTask Configuration")
        table.add_column("Setting")
        table.add_column("Value")
        
        table.add_row("API Key", masked_key)
        table.add_row("Default Priority", default_priority)
        
        console.print(table)


# Add task command
@cli.command()
@click.argument("description")
@click.option("--priority", help="Task priority (high, medium, low)", 
              callback=validate_priority)
@click.option("--due", help="Due date/time in natural language (e.g., 'tomorrow at 5pm')")
@click.option("--context", help="Task context (e.g., 'work', 'personal')")
@click.option("--project", help="Project the task belongs to")
def add(description, priority, due, context, project):
    """Add a new task."""
    # Use default priority if not specified
    if not priority:
        priority = get_config_value("priority_default", "medium")
    
    # Process due date if provided
    due_date_time = None
    if due:
        if check_gemini_api_key():
            due_date_time = utils.extract_date_time(due)
            if not due_date_time:
                console.print(f"[yellow]Warning: Could not parse date '{due}'. No due date set.[/yellow]")
        else:
            console.print("[yellow]Skipping due date processing. Set Gemini API key for this feature.[/yellow]")
    
    # Add the task
    result = db.add_task(description, priority, due_date_time, context, project)
    
    if result["success"]:
        task = result["task"]
        console.print(f"[green]Task added successfully with ID: {task['id']}[/green]")
        
        # Display the added task
        task_list = [task]
        console.print(format_table_output(task_list))
    else:
        console.print(f"[red]Error adding task: {result.get('error', 'Unknown error')}[/red]")


# List tasks command
@cli.command()
@click.option("--all", is_flag=True, help="List all tasks, including completed ones")
@click.option("--priority", help="Filter by priority (high, medium, low)", 
              callback=validate_priority)
@click.option("--due", help="Filter by due date range (e.g., 'today', 'this week')")
@click.option("--context", help="Filter by context")
@click.option("--project", help="Filter by project")
@click.option("--overdue", is_flag=True, help="Show only overdue tasks")
@click.option("--completed", is_flag=True, help="Show only completed tasks")
def list(all, priority, due, context, project, overdue, completed):
    """List tasks with optional filters."""
    due_range = None
    
    if due:
        if check_gemini_api_key():
            due_range = utils.parse_date_range(due)
            if not due_range or (not due_range[0] and not due_range[1]):
                console.print(f"[yellow]Warning: Could not parse date range '{due}'. Showing all dates.[/yellow]")
        else:
            console.print("[yellow]Skipping date range processing. Set Gemini API key for this feature.[/yellow]")
    
    # Get tasks with filters
    tasks = db.list_tasks(
        all_tasks=all,
        priority=priority,
        due_range=due_range,
        context_name=context,
        project_name=project,
        overdue=overdue,
        completed=completed
    )
    
    if tasks:
        console.print(f"Found {len(tasks)} tasks:")
        console.print(format_table_output(tasks))
    else:
        console.print("No tasks found matching your criteria.")


# Mark task as done command
@cli.command()
@click.argument("task_id", type=int)
def done(task_id):
    """Mark a task as completed."""
    task = db.get_task(task_id)
    
    if not task:
        console.print(f"[red]Error: Task with ID {task_id} not found.[/red]")
        return
    
    if task["completed"]:
        console.print(f"[yellow]Task {task_id} is already marked as completed.[/yellow]")
        return
    
    result = db.mark_task_done(task_id)
    
    if result["success"]:
        console.print(f"[green]Task {task_id} marked as completed:[/green]")
        updated_task = db.get_task(task_id)
        console.print(format_table_output([updated_task]))
    else:
        console.print(f"[red]Error marking task as done: {result.get('error', 'Unknown error')}[/red]")


# Edit task command
@cli.command()
@click.argument("task_id", type=int)
@click.option("--description", help="New task description")
@click.option("--priority", help="New priority (high, medium, low)", 
              callback=validate_priority)
@click.option("--due", help="New due date/time in natural language")
@click.option("--context", help="New context")
@click.option("--project", help="New project")
def edit(task_id, description, priority, due, context, project):
    """Edit an existing task."""
    task = db.get_task(task_id)
    
    if not task:
        console.print(f"[red]Error: Task with ID {task_id} not found.[/red]")
        return
    
    # If any option was provided, update the task
    if any([description, priority, due, context, project is not None]):
        # Process due date if provided
        due_date_time = None
        if due:
            if check_gemini_api_key():
                due_date_time = utils.extract_date_time(due)
                if not due_date_time:
                    console.print(f"[yellow]Warning: Could not parse date '{due}'. Keeping existing due date.[/yellow]")
            else:
                console.print("[yellow]Skipping due date processing. Set Gemini API key for this feature.[/yellow]")
        
        # Update the task
        result = db.edit_task(
            task_id,
            description=description,
            priority=priority,
            due_date_time=due_date_time if due else None,
            context_name=context,
            project_name=project
        )
        
        if result["success"]:
            console.print(f"[green]Task {task_id} updated successfully:[/green]")
            console.print(format_table_output([result["task"]]))
        else:
            console.print(f"[red]Error updating task: {result.get('error', 'Unknown error')}[/red]")
    else:
        console.print("[yellow]No changes specified. Task remains unchanged.[/yellow]")
        console.print(format_table_output([task]))


# Delete task command
@cli.command()
@click.argument("task_id", type=int)
@click.option("--force", is_flag=True, help="Delete without confirmation")
def delete(task_id, force):
    """Delete a task."""
    task = db.get_task(task_id)
    
    if not task:
        console.print(f"[red]Error: Task with ID {task_id} not found.[/red]")
        return
    
    # Show the task to be deleted
    console.print("Task to delete:")
    console.print(format_table_output([task]))
    
    # Confirm deletion unless --force is used
    if not force and not click.confirm("Are you sure you want to delete this task?"):
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return
    
    result = db.delete_task(task_id)
    
    if result["success"]:
        console.print(f"[green]Task {task_id} deleted successfully.[/green]")
    else:
        console.print(f"[red]Error deleting task: {result.get('error', 'Unknown error')}[/red]")


# Suggest due date command
@cli.command(name="suggest-due")
@click.argument("task_description")
def suggest_due(task_description):
    """Suggest a due date based on the task description."""
    if not check_gemini_api_key():
        return
    
    console.print("Analyzing task description...")
    
    suggested_date = utils.suggest_due_date(task_description)
    
    if suggested_date:
        formatted_date = utils.format_relative_date(suggested_date)
        console.print(f"[green]Suggested due date: {formatted_date}[/green]")
        console.print(f"Raw date: {suggested_date}")
    else:
        console.print("[yellow]Could not suggest a due date for this task.[/yellow]")


# Context management commands
@cli.command(name="add-context")
@click.argument("name")
def add_context(name):
    """Add a new context."""
    result = db.add_context(name)
    
    if result["success"]:
        console.print(f"[green]Context '{name}' added successfully.[/green]")
    else:
        console.print(f"[red]Error adding context: {result.get('error', 'Unknown error')}[/red]")


@cli.command(name="list-contexts")
def list_contexts():
    """List all contexts."""
    contexts = db.list_contexts()
    
    if contexts:
        table = Table(show_header=True, title="Contexts")
        table.add_column("ID")
        table.add_column("Name")
        
        for context in contexts:
            table.add_row(str(context["id"]), context["name"])
        
        console.print(table)
    else:
        console.print("No contexts found.")


# Project management commands
@cli.command(name="add-project")
@click.argument("name")
def add_project(name):
    """Add a new project."""
    result = db.add_project(name)
    
    if result["success"]:
        console.print(f"[green]Project '{name}' added successfully.[/green]")
    else:
        console.print(f"[red]Error adding project: {result.get('error', 'Unknown error')}[/red]")


@cli.command(name="list-projects")
def list_projects():
    """List all projects."""
    projects = db.list_projects()
    
    if projects:
        table = Table(show_header=True, title="Projects")
        table.add_column("ID")
        table.add_column("Name")
        
        for project in projects:
            table.add_row(str(project["id"]), project["name"])
        
        console.print(table)
    else:
        console.print("No projects found.")


if __name__ == "__main__":
    cli()
