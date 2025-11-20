# recommender.py
import click
import database
from datetime import datetime, timedelta
# Removed circular import - moved to function level

def provide_guidance(conn, event):
    """
    分析刚刚记录的事件，并提供上下文感知的“下一步指导”。
    """
    # Lazy import to avoid circular dependency
    from analysis import get_energy_assessment
    
    key_state = event["key_state"]
    c = conn.cursor()

    if key_state == "Internal friction":
        click.echo(click.style("\n[指导]：检测到 '内耗' 状态。这是一个行动信号！", fg="yellow"))
        
        # 1. (不变) 检查客观能量状态
        try:
            assessment = get_energy_assessment(conn)
            if assessment['state'] == 'Fatigued' or assessment['state'] == 'Stressed':
                 # (如果疲劳，建议休息，逻辑不变)
                 click.echo(click.style(f"客观数据：你当前状态为 '{assessment['state']}'。", fg="red"))
                 for msg in assessment['messages']:
                      if "警告" in msg: click.echo(click.style(f"  {msg}", fg="red"))
                 click.echo("\n建议：你的 '内耗' 很可能来自 '体能' 或 '情绪' 耗尽。")
                 click.echo("优先执行 '充沛' (Abundance) 任务 (如 冥想, 散步)，不要强迫自己执行 '成长' (Growth) 任务。")
                 return
        except Exception:
             pass
        
        # 2. --- 升级：只推荐 P1 任务 ---
        # (如果能量充足，但仍在内耗)
        click.echo("你的能量储备尚可，但你正陷入“内耗”（拖延）。")

        # --- 新增：检查 P/M/E 分数 ---
        if event.get('mental_score', 10) < 4:
            click.echo(click.style("...但你的'脑力'分数偏低。这可能是'启动阻力'。", fg="yellow"))
            click.echo(click.style("建议：从一个*极小*的 P1 任务开始（例如‘只看5个雅思单词’），而不是一个15分钟的任务。", bold=True))
            return
        
        if event.get('emotional_score', 10) < 4:
            click.echo(click.style("...但你的'情绪'分数偏低。", fg="yellow"))
            click.echo(click.style("建议：先执行一个 10 分钟的 'Abundance (充沛)' 任务（如冥想或听音乐），*然后再*切换到 P1 任务。", bold=True))
            return
        # --- 新增结束 ---

        c.execute("""
            SELECT e.activity, g.goal_name
            FROM events e
            JOIN goals g ON e.goal_id = g.goal_id
            WHERE (e.key_state = 'Growth' OR e.key_state = 'Abundance')
              AND g.priority_level = 1
              AND e.duration_minutes <= 30
            ORDER BY e.timestamp_start DESC
            LIMIT 1
        """)
        rec = c.fetchone()
        
        if rec:
            activity, goal_name = rec
            click.echo(f"建议：你上一次的 **P1-高优先级** 微型任务是 '{activity}' (目标: {goal_name})。")
            click.echo(click.style("立即执行一个15分钟的“高优先级”微型任务（如“10个雅思单词”），来打破这个拖延循环。", bold=True))
        else:
            click.echo(click.style("建议：立即开始一个15分钟的 **P1-高优先级** 任务（雅思或作业），来打破这个拖延循环。", bold=True))
        # --- 升级结束 ---

    elif key_state == "Consumption":
        # (此逻辑不变)
        click.echo(click.style("\n[指导]：检测到 '消耗' 状态。是时候主动恢复了。", fg="cyan"))
        c.execute("""
            SELECT activity, COUNT(*) as count FROM events
            WHERE key_state = 'Abundance'
            GROUP BY activity
            ORDER BY count DESC
            LIMIT 1
        """)
        rec = c.fetchone()
        if rec:
            click.echo(f"建议：数据显示 '{rec[0]}' 经常带给你 '充沛' 感。")
            click.echo("尝试花10-15分钟进行此活动（如散步、冥想），而不是被动刷手机。")
        else:
            click.echo("建议：进行10-15分钟的主动休息（如散步、冥想）来恢复能量。")

    elif key_state == "Growth" or key_state == "Abundance":
        # (此逻辑不变)
        click.echo(click.style(f"\n[指导]：非常棒！你记录了一个 '{key_state}' 事件。", fg="green"))
        if event["goal_id"]:
            goal = database.get_goal_by_id(conn, event["goal_id"])
            if goal:
                click.echo(f"你正在为目标 '{goal[1]}' 积累积极的能量。保持这个势头！")
        else:
            click.echo("你刚刚完成了一次高质量的能量补充。做得好！")

    elif key_state == "Routine":
        # (此逻辑不变)
        click.echo(click.style("\n[指导]：已记录 '常规' 任务。", fg="white"))
        click.echo("这是一个很好的过渡点。考虑现在开始一个与你核心目标（如雅思、作业）相关的“25分钟番茄钟”。")


def get_sleep_recommendation(conn):
    """
    分析过去7天的睡眠数据，提供睡眠建议。
    """
    c = conn.cursor()
    seven_days_ago = (datetime.now() - timedelta(days=7)).date()

    c.execute("""
        SELECT value_numeric FROM health_metrics
        WHERE metric_type = 'sleep_total_min' AND DATE(timestamp) >= ?
    """, (seven_days_ago,))
    
    sleep_data = c.fetchall()
    
    if not sleep_data or len(sleep_data) < 3:
        return "睡眠数据不足 (少于3天)，无法生成建议。"

    total_minutes = sum(item[0] for item in sleep_data)
    avg_minutes = total_minutes / len(sleep_data)
    avg_hours = avg_minutes / 60

    recommendation = f"过去7天，你平均睡眠 {avg_hours:.1f} 小时。"
    if avg_hours < 7.5:
        recommendation += " 低于推荐的8小时。试着今晚早睡30分钟。"
    else:
        recommendation += " 做得很好！请继续保持。"
        
    return recommendation

def get_exercise_recommendation(conn):
    """
    根据昨日的恢复数据和主观记录，提供今日的运动建议。
    """
    c = conn.cursor()
    yesterday = (datetime.now() - timedelta(days=1)).date()

    # 1. 获取昨日的关键恢复指标
    c.execute("""
        SELECT metric_type, value_numeric FROM health_metrics
        WHERE DATE(timestamp) = ? AND metric_type IN ('sleep_score', 'rhr_avg')
    """, (yesterday,))
    
    yesterday_metrics = dict(c.fetchall())
    sleep_score = yesterday_metrics.get('sleep_score', 0)
    rhr_avg = yesterday_metrics.get('rhr_avg', 0)

    # 2. 获取静息心率基线
    seven_days_ago = (datetime.now() - timedelta(days=8)).date()
    c.execute("""
        SELECT AVG(value_numeric) FROM health_metrics
        WHERE metric_type = 'rhr_avg' AND value_numeric > 0 AND DATE(timestamp) >= ? AND DATE(timestamp) < ?
    """, (seven_days_ago, yesterday))
    rhr_baseline_data = c.fetchone()
    rhr_baseline = rhr_baseline_data[0] if rhr_baseline_data and rhr_baseline_data[0] else rhr_avg or 60

    # 3. 获取昨日的“内耗”总时长
    c.execute("""
        SELECT SUM(duration_minutes) FROM events
        WHERE key_state = 'Internal friction' AND DATE(timestamp_start) = ?
    """, (yesterday,))
    friction_minutes_data = c.fetchone()
    friction_hours = (friction_minutes_data[0] / 60) if friction_minutes_data and friction_minutes_data[0] else 0

    # --- 生成建议的规则引擎 ---
    if sleep_score > 0 and sleep_score < 70:
        return f"恢复预警：昨日睡眠分数 ({sleep_score}) 较低。建议进行轻度活动，如20分钟散步或拉伸，避免高强度训练。"
        
    if rhr_avg > 0 and rhr_avg > rhr_baseline + 4:
        return f"恢复预警：昨日静息心率 ({rhr_avg:.0f}) 显著高于基线 ({rhr_baseline:.0f})。身体可能未完全恢复，建议休息或只进行轻度活动。"

    if friction_hours > 2:
        return f"精神疲劳：昨日记录了 {friction_hours:.1f} 小时的'内耗'。高强度的精神消耗会影响身体。建议进行恢复性活动，如瑜伽或散步，来调整状态。"

    return "恢复良好：你的身体和精神状态指标良好。今天是进行中高强度训练（如有氧运动或力量训练）的好时机。"