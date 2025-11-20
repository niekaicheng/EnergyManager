
# database.py
import sqlite3
import click

def create_connection():
    """Creates a database connection."""
    conn = sqlite3.connect("emanager.db")
    return conn

def migrate_db(conn):
    """Applies database migrations."""
    c = conn.cursor()
    
    # 检查 "goals" 表中是否存在 "energy_cost" 列
    c.execute("PRAGMA table_info(goals)")
    columns = [col[1] for col in c.fetchall()]
    
    if "energy_cost" not in columns:
        click.echo(click.style("Applying database migration: Adding 'energy_cost' to 'goals' table...", fg="yellow"))
        c.execute("ALTER TABLE goals ADD COLUMN energy_cost INTEGER DEFAULT 0")
        conn.commit()

def create_tables(conn):
    """Creates the goals, events, and health_metrics tables."""
    c = conn.cursor()
    
    # --- 升级 "goals" 表 ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            goal_id INTEGER PRIMARY KEY,
            goal_name TEXT NOT NULL UNIQUE,
            priority_level INTEGER DEFAULT 2,  -- 1=High, 2=Medium, 3=Low/Procrastination
            is_active BOOLEAN DEFAULT 1,
            energy_cost INTEGER DEFAULT 0
        )
    """)
    # --- 升级结束 ---

    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            timestamp_start DATETIME,
            duration_minutes INTEGER NOT NULL,
            activity TEXT NOT NULL,
            goal_id INTEGER,
            physical_score INTEGER,
            mental_score INTEGER,
            emotional_score INTEGER,
            key_state TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            metric_id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            metric_type TEXT NOT NULL,
            value_numeric REAL,
            value_text TEXT,
            source TEXT DEFAULT 'MiBand',
            UNIQUE(timestamp, metric_type)
        )
    """)
    
    conn.commit()

# --- 升级 "add_goal" 函数 ---
def add_goal(conn, goal_name, priority_level, energy_cost):
    """Adds a new goal to the goals table with a priority and energy_cost."""
    c = conn.cursor()
    c.execute("INSERT INTO goals (goal_name, priority_level, energy_cost) VALUES (?, ?, ?)", (goal_name, priority_level, energy_cost))
    conn.commit()
# --- 升级结束 ---

def get_active_goals(conn):
    """Gets all active goals from the goals table, including priority."""
    c = conn.cursor()
    # --- 升级：获取 priority_level ---
    c.execute("SELECT goal_id, goal_name, priority_level, energy_cost FROM goals WHERE is_active = 1 ORDER BY priority_level, goal_name")
    return c.fetchall()
    # --- 升级结束 ---

def archive_goal_by_id(conn, goal_id):
    """Archives a goal in the goals table by its ID."""
    c = conn.cursor()
    c.execute("UPDATE goals SET is_active = 0 WHERE goal_id = ?", (goal_id,))
    conn.commit()

def get_goal_by_id(conn, goal_id):
    """Fetches a single goal by its ID."""
    c = conn.cursor()
    c.execute("SELECT * FROM goals WHERE goal_id = ?", (goal_id,))
    return c.fetchone()

def insert_event(conn, event):
    """Inserts a new event into the events table."""
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (
            timestamp_start,
            duration_minutes,
            activity,
            goal_id,
            physical_score,
            mental_score,
            emotional_score,
            key_state,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event["timestamp_start"],
        event["duration_minutes"],
        event["activity"].encode('utf-8', 'surrogateescape').decode('utf-8'),
        event["goal_id"],
        event["physical_score"],
        event["mental_score"],
        event["emotional_score"],
        event["key_state"].encode('utf-8', 'surrogateescape').decode('utf-8'),
        event["notes"].encode('utf-8', 'surrogateescape').decode('utf-8'),
    ))
    conn.commit()

def insert_health_metrics_batch(conn, metrics_data):
    """
    Inserts a batch of health metrics into the database.
    """
    c = conn.cursor()
    c.executemany("""
        INSERT OR IGNORE INTO health_metrics (timestamp, metric_type, value_numeric, value_text)
        VALUES (?, ?, ?, ?)
    """, metrics_data)
    conn.commit()


# (将其添加到 database.py 中，替换掉上次的 update_goal_cost)
# (get_goal_by_id 函数 保持不变)

def update_goal(conn, goal_id, new_name=None, new_cost=None, new_priority=None):
    """
    更新一个目标的名称、成本或优先级。
    只更新提供了新值的字段 (非 None)。
    """
    c = conn.cursor()

    updates = []
    params = []

    if new_name is not None:
        updates.append("goal_name = ?")
        params.append(new_name)

    if new_cost is not None:
        updates.append("energy_cost = ?")
        params.append(new_cost)

    if new_priority is not None:
        updates.append("priority_level = ?")
        params.append(new_priority)

    if not updates:
        # 没有请求任何更改
        return 0

        # 动态构建 SQL 语句
    sql = f"UPDATE goals SET {', '.join(updates)} WHERE goal_id = ?"
    params.append(goal_id)

    c.execute(sql, tuple(params))
    conn.commit()

    # 返回受影响的行数
    return c.rowcount