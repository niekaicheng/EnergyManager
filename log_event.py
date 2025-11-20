
# log_event.py
import click
import database
from datetime import datetime
from constants import KEY_STATE_CHOICES
import recommender

def prompt_for_log(default_activity=None, default_duration=None):
    """Prompts the user to log an event, with optional default values."""
    if default_activity:
        activity = click.prompt("What activity did you just complete?", default=default_activity)
    else:
        activity = click.prompt("What activity did you just complete?")

    if default_duration:
        duration_minutes = click.prompt("How long did it take (in minutes)?", type=int, default=default_duration)
    else:
        duration_minutes = click.prompt("How long did it take (in minutes)?", type=int)
    
    conn = database.create_connection()
    goals = database.get_active_goals(conn)
    
    goal_id = None
    if goals:
        click.echo("Do you want to associate this activity with a goal?")
        valid_ids = []
        
        # --- 升级：显示优先级 ---
        current_priority = 0
        for goal in goals:
            goal_id_num, goal_name, priority, energy_cost = goal
            
            # 打印优先级标题
            if priority != current_priority:
                priority_label = {1: "P1-High", 2: "P2-Medium", 3: "P3-Low"}.get(priority)
                click.echo(click.style(f"--- {priority_label} ---", bold=(priority==1)))
                current_priority = priority
                
            click.echo(f"  [{goal_id_num}] {goal_name} (Cost: {energy_cost})")
            valid_ids.append(str(goal_id_num))
        # --- 升级结束 ---
            
        while True:
            goal_choice = click.prompt("Enter the goal number or 'N' for none", default="N")
            if goal_choice.upper() == 'N':
                goal_id = None
                break
            elif goal_choice in valid_ids:
                goal_id = int(goal_choice)
                break
            else:
                click.echo(click.style(f"输入无效。请输入 {valid_ids} 中的一个数字或 'N'。", fg="red"))
            
    else:
        goal_id = None

    physical_score = click.prompt("Rate your physical energy at the end (1-10)", type=int)
    mental_score = click.prompt("Rate your mental energy at the end (1-10)", type=int)
    emotional_score = click.prompt("Rate your emotional energy at the end (1-10)", type=int)

    click.echo("What is your key state?")
    state_options = list(KEY_STATE_CHOICES.keys())
    valid_state_choices = []
    
    for i, key in enumerate(state_options):
        description = KEY_STATE_CHOICES[key] 
        click.echo(f"[{i+1}] {key} ({description})")
        valid_state_choices.append(str(i+1))

    while True:
        choice = click.prompt("Enter the number", type=str)
        if choice in valid_state_choices:
            key_state = state_options[int(choice) - 1]
            break
        else:
            click.echo(click.style(f"输入无效。请输入 {valid_state_choices} 中的一个数字。", fg="red"))
    
    notes = click.prompt("Any additional notes?", default="", show_default=False)

    event = {
        "timestamp_start": datetime.now(),
        "duration_minutes": duration_minutes,
        "activity": activity.encode('utf-8', 'surrogateescape').decode('utf-8'),
        "goal_id": goal_id,
        "physical_score": physical_score,
        "mental_score": mental_score,
        "emotional_score": emotional_score,
        "key_state": key_state,
        "notes": notes.encode('utf-8', 'surrogateescape').decode('utf-8'),
    }

    database.insert_event(conn, event)
    click.echo(click.style("Event logged successfully!", fg="green"))

    # recommender.py 现在也会被升级
    recommender.provide_guidance(conn, event)
    conn.close()

@click.command()
def log():
    """Logs a new event and provides immediate guidance."""
    prompt_for_log()

