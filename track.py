# track.py
import click
import os
from datetime import datetime
import log_event

ACTIVE_TASK_FILE = ".active_task" # 跟踪当前任务

@click.command()
@click.argument("activity")
def start(activity):
    """Starts tracking a new activity."""
    if os.path.exists(ACTIVE_TASK_FILE):
        click.echo(f"Error: Another task is already running. Run 'emanager stop' first.", err=True)
        return
    
    with open(ACTIVE_TASK_FILE, "w") as f:
        f.write(f"{activity}\n{datetime.now().isoformat()}") # 存储活动和时间
    click.echo(click.style(f"Timer started for: {activity}", fg="green"))

@click.command()
def stop():
    """Stops the active task and prompts for logging."""
    if not os.path.exists(ACTIVE_TASK_FILE):
        click.echo("No task is currently running. Use 'emanager log' or 'emanager start'.", err=True)
        return

    with open(ACTIVE_TASK_FILE, "r") as f:
        lines = f.readlines()
        activity = lines[0].strip()
        start_time = datetime.fromisoformat(lines[1].strip())
    
    os.remove(ACTIVE_TASK_FILE) # 删除跟踪文件
    
    duration = (datetime.now() - start_time).total_seconds() / 60
    
    click.echo(click.style(f"Timer stopped for: {activity}", fg="green"))
    click.echo(f"Duration: {duration:.0f} minutes.")
    
    # --- 关键：提示用户记录 ---
    click.echo("\nPlease log the energy details for this completed task.")
    log_event.prompt_for_log(default_activity=activity, default_duration=int(duration))
