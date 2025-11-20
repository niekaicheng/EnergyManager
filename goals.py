# goals.py
import click
import database
import sqlite3

@click.group()
def goal():
    """Manage your goals."""
    pass

@goal.command()
@click.argument("goal_name")
# --- 升级：添加 --priority 选项 ---
@click.option('--priority', default=2, type=click.Choice(['1', '2', '3']),
              help='Priority (1=High, 2=Medium, 3=Low/Procrastination)')
@click.option('--cost', type=int, default=0, help='此任务的能量成本 (消耗为负, 恢复为正)')
# --- 升级结束 ---
def add(goal_name, priority, cost):
    """Adds a new goal."""
    conn = database.create_connection()
    try:
        database.add_goal(conn, goal_name, int(priority), cost)
        click.echo(f"Added (P{priority}, Cost: {cost}) goal: {goal_name}")
    except Exception as e:
        click.echo(f"Error adding goal: {e}", err=True)
    finally:
        conn.close()

@goal.command()
def list():
    """Lists all active goals by priority."""
    conn = database.create_connection()
    goals = database.get_active_goals(conn)
    conn.close()

    if not goals:
        click.echo("No active goals found. Use 'emanager goal add' to create one.")
        return

    click.echo(click.style("--- Active Goals by Priority ---", bold=True))
    
    # --- 升级：按优先级打印 ---
    current_priority = 0
    for g in goals:
        goal_id, goal_name, priority, energy_cost = g
        if priority != current_priority:
            priority_label = {1: "High (P1)", 2: "Medium (P2)", 3: "Low/Procrastination (P3)"}.get(priority)
            click.echo(click.style(f"\n{priority_label}:", bold=True))
            current_priority = priority
        click.echo(f"  [{goal_id}] {goal_name} (Cost: {energy_cost})")
    # --- 升级结束 ---

@goal.command()
@click.argument("goal_id", type=int)
def archive(goal_id):
    """Archives a goal using its ID."""
    conn = database.create_connection()
    
    goal = database.get_goal_by_id(conn, goal_id)
    if not goal:
        click.echo(f"Error: Goal with ID {goal_id} not found.", err=True)
        conn.close()
        return

    if click.confirm(f"Are you sure you want to archive goal: '{goal[1]}'?"):
        database.archive_goal_by_id(conn, goal_id)
        click.echo(f"Goal '{goal[1]}' (ID: {goal_id}) archived.")
    else:
        click.echo("Archive cancelled.")
    
    conn.close()

    # (在文件末尾添加这个新命令)
    # (它替换了我上次给您的 update 命令)

@goal.command()
@click.argument("goal_id", type=int)
@click.option('--name', type=str, default=None, help='任务的新名称。')
@click.option('--cost', type=int, default=None, help='任务的新能量成本。')
@click.option('--priority', type=click.Choice(['1', '2', '3']), default=None, help='任务的新优先级 (1, 2, or 3)。')
def update(goal_id, name, cost, priority):
    """
    更新一个现有目标的详细信息 (名称, 成本, 优先级)。
    """
    conn = database.create_connection()

    if name is None and cost is None and priority is None:
        click.echo("错误: 您必须至少提供一个要更新的选项 (--name, --cost, 或 --priority)。", err=True)
        conn.close()
        return

    try:
        # 1. 检查目标是否存在
        goal = database.get_goal_by_id(conn, goal_id)
        if not goal:
            click.echo(f"错误: 未找到 ID 为 {goal_id} 的目标。", err=True)
            conn.close()
            return

        goal_name_orig = goal[1]

        # 2. 执行更新
        # database.update_goal 函数会处理 None 值
        rowcount = database.update_goal(
            conn,
            goal_id,
            new_name=name,
            new_cost=cost,
            new_priority=(int(priority) if priority else None)
        )

        if rowcount > 0:
            click.echo(click.style(f"成功! 目标 '{goal_name_orig}' (ID: {goal_id}) 已被更新。", fg="green"))

            # 明确显示哪些内容被更改了
            if name:
                click.echo(f"  - 名称更新为: {name}")
            if cost is not None:  # 0 也是一个有效的成本
                click.echo(f"  - 成本更新为: {cost}")
            if priority:
                click.echo(f"  - 优先级更新为: P{priority}")
        else:
            click.echo(f"未对目标 ID {goal_id} 进行任何更改。")

    except sqlite3.IntegrityError as e:
        # 捕获数据库错误，例如尝试重命名为一个已存在的名称
        if "UNIQUE constraint failed: goals.goal_name" in str(e):
            click.echo(click.style(f"错误: 名为 '{name}' 的目标已存在。请选择一个唯一的名称。", fg="red"), err=True)
        else:
            click.echo(f"数据库错误: {e}", err=True)
    except Exception as e:
        click.echo(f"发生错误: {e}", err=True)
    finally:
        conn.close()