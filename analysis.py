# analysis.py
# (放在 analysis.py 顶部)
import pandas as pd
import matplotlib
matplotlib.use('Agg') # 关键：设置为“非交互式”后端，防止GUI窗口
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
import click
import recommender
import database
from datetime import datetime, timedelta

# (get_energy_assessment 函数保持不变)
# (替换 analysis.py 中的旧 get_energy_assessment 函数)
def get_energy_assessment(conn, reference_date=None):
    """
    分析指定日期的心率和睡眠数据，评估能量状态。
    如果 reference_date 为 None，则默认为今天。
    """
    if reference_date is None:
        reference_date = datetime.now().date()

    ref_date_str = reference_date.isoformat()
    # 基线计算需要前7天和前3天的数据
    seven_days_ago_str = (reference_date - timedelta(days=7)).isoformat()
    three_days_ago_str = (reference_date - timedelta(days=3)).isoformat()

    c = conn.cursor()
    
    # 1. 获取当天的睡眠数据
    c.execute("""
        SELECT value_numeric FROM health_metrics
        WHERE metric_type = 'sleep_total_min' AND DATE(timestamp) = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (ref_date_str,))
    sleep_data = c.fetchone()
    sleep_hours = (sleep_data[0] / 60) if sleep_data else 0

    # 2. 获取当天的静息心率 (RHR)
    c.execute("""
        SELECT value_numeric FROM health_metrics
        WHERE metric_type = 'rhr_avg' AND value_numeric > 0 AND DATE(timestamp) = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (ref_date_str,))
    rhr_data = c.fetchone()
    latest_rhr = rhr_data[0] if rhr_data else 0

    # 3. 获取前7天的 RHR 基线 (不包括当天)
    c.execute("""
        SELECT AVG(value_numeric) FROM health_metrics
        WHERE metric_type = 'rhr_avg' AND value_numeric > 0
          AND DATE(timestamp) >= ? AND DATE(timestamp) < ?
    """, (seven_days_ago_str, ref_date_str))
    rhr_baseline_data = c.fetchone()
    rhr_baseline = rhr_baseline_data[0] if rhr_baseline_data and rhr_baseline_data[0] else 60

    # 4. 获取当天的压力
    c.execute("""
        SELECT value_numeric FROM health_metrics
        WHERE metric_type = 'stress_avg' AND value_numeric > 0 AND DATE(timestamp) = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (ref_date_str,))
    stress_data = c.fetchone()
    latest_stress = stress_data[0] if stress_data else 0

    # 5. 获取前3天的平均训练负荷 (不包括当天)
    c.execute("""
        SELECT AVG(value_numeric) FROM health_metrics
        WHERE metric_type = 'workout_train_load' AND value_numeric > 0
          AND DATE(timestamp) >= ? AND DATE(timestamp) < ?
    """, (three_days_ago_str, ref_date_str))
    train_load_data = c.fetchone()
    avg_train_load = train_load_data[0] if train_load_data and train_load_data[0] else 0

    # (评估逻辑保持不变)
    assessment = {
        'state': 'Ready',
        'sleep_hours': sleep_hours,
        'latest_rhr': latest_rhr,
        'rhr_baseline': rhr_baseline,
        'latest_stress': latest_stress,
        'avg_train_load': avg_train_load,
        'messages': []
    }

    if sleep_hours > 0 and sleep_hours < 7:
        assessment['state'] = 'Fatigued'
        assessment['messages'].append(f"警告: 睡眠不足 ({sleep_hours:.1f} 小时)。体能储备较低。")

    if latest_rhr > 0 and rhr_baseline > 0 and latest_rhr > (rhr_baseline + 4):
        assessment['state'] = 'Stressed'
        assessment['messages'].append(f"警告: 静息心率偏高 ({latest_rhr:.0f} bpm)，高于你的基线 ({rhr_baseline:.0f} bpm)。身体未完全恢复。")

    if latest_stress > 40:
        assessment['state'] = 'Stressed'
        assessment['messages'].append(f"警告: 平均压力水平偏高 ({latest_stress:.0f})。情绪能量较低。")

    if avg_train_load > 120:
        assessment['state'] = 'Fatigued'
        assessment['messages'].append(f"警告: 过去3天平均训练负荷过高 ({avg_train_load:.0f})。身体处于疲劳状态，即使睡眠尚可。")

    if assessment['state'] == 'Ready' and sleep_hours > 0:
        assessment['messages'].append("数据：睡眠充足，心率正常。能量储备良好。")
    elif sleep_hours == 0 and latest_rhr == 0:
        assessment['state'] = 'No Data'
        assessment['messages'].append("警告: 缺少当日的客观健康数据。")


    return assessment


def get_daily_energy_budget(conn, reference_date=None):
    """
    根据健康数据计算每日能量预算。
    基础预算根据睡眠质量和恢复状态调整。
    
    返回一个整数，代表今日可用的能量点数。
    """
    if reference_date is None:
        reference_date = datetime.now().date()
    
    assessment = get_energy_assessment(conn, reference_date)
    
    # 基础预算（默认值）
    base_budget = 50
    
    # 根据状态调整预算
    if assessment['state'] == 'No Data':
        # 没有数据时给予平均预算
        return base_budget
    
    # 根据睡眠时长调整
    sleep_hours = assessment.get('sleep_hours', 0)
    if sleep_hours >= 8:
        base_budget += 20  # 睡眠充足，+20
    elif sleep_hours >= 7:
        base_budget += 10  # 睡眠良好，+10
    elif sleep_hours >= 6:
        base_budget += 0   # 睡眠一般，不变
    elif sleep_hours > 0:
        base_budget -= 20  # 睡眠不足，-20
    
    # 根据心率恢复调整
    rhr = assessment.get('latest_rhr', 0)
    rhr_baseline = assessment.get('rhr_baseline', 0)
    if rhr > 0 and rhr_baseline > 0:
        rhr_diff = rhr - rhr_baseline
        if rhr_diff > 5:
            base_budget -= 15  # 心率偏高，身体压力大
        elif rhr_diff > 2:
            base_budget -= 10  # 心率略高
        elif rhr_diff < -2:
            base_budget += 10  # 心率偏低，恢复良好
    
    # 根据压力水平调整
    stress = assessment.get('latest_stress', 0)
    if stress > 50:
        base_budget -= 15  # 高压力
    elif stress > 30:
        base_budget -= 5   # 中等压力
    
    # 根据训练负荷调整
    train_load = assessment.get('avg_train_load', 0)
    if train_load > 120:
        base_budget -= 20  # 高训练负荷，需要更多恢复
    elif train_load > 90:
        base_budget -= 10  # 中等训练负荷
    
    # 确保预算不为负数，最低为5
    return max(5, base_budget)


# --- 升级：新增的进度条辅助函数 ---
def _create_bar_and_color(value, thresholds, bar_length=10):
    """
    根据值和阈值创建进度条和颜色。
    thresholds = [yellow_start, green_start, range_end_or_min]
    """
    if value is None:
        return '░' * bar_length, "white"

    t_thresh_1 = thresholds[0]  # 黄色区域起点 (或红色区域终点)
    t_thresh_2 = thresholds[1]  # 绿色区域起点 (或黄色区域终点)
    t_range_ref = thresholds[2]  # 进度条的 "100%" 参考点

    # 检查是“越高越好” (e.g., 60 < 75 for sleep) 还是“越低越好” (e.g., 68 > 63 for RHR)
    is_increasing = t_thresh_1 < t_thresh_2

    color = "white"
    percent = 0.0

    if is_increasing:
        # 越高越好 (e.g., sleep_score [60, 75, 100])
        # 进度条的100%点是 t_range_ref (e.g., 100)
        bar_max = t_range_ref
        if bar_max <= 0: bar_max = t_thresh_2  # 避免除零
        percent = value / bar_max

        # 决定颜色
        if value >= t_thresh_2:
            color = "green"
        elif value >= t_thresh_1:
            color = "yellow"
        else:
            color = "red"

    else:
        # 越低越好 (e.g., rhr_avg [68, 63, 50] or train_load [120, 90, 0])
        # 进度条的100%点应该是 "红色" 的起点 (e.g., 68 for RHR, 120 for Train Load)
        bar_max = t_thresh_1
        if bar_max <= 0: bar_max = 1  # 避免除零
        percent = value / bar_max  # e.g., 165 / 120 = 137.5%

        # 决定颜色
        if value <= t_thresh_2:
            color = "green"
        elif value <= t_thresh_1:
            color = "yellow"
        else:
            color = "red"

    # 限制进度条在 0% 到 100% 之间 (即使数值超出)
    percent = max(0.0, min(1.0, percent))

    filled_blocks = int(round(percent * bar_length))
    empty_blocks = bar_length - filled_blocks
    bar_str = '█' * filled_blocks + '░' * empty_blocks

    return bar_str, color


# --- 辅助函数结束 ---
# (print_health_analysis 函数保持不变)
def print_health_analysis(health_stats):
    """
    将健康统计数据转换为带颜色和解释的用户友好输出。
    """
    click.echo(click.style("\n--- 客观健康指标分析 (Health Metrics Analysis) ---", bold=True, fg="blue"))
    stats_dict = {}
    for metric_name, avg_val, sum_val in health_stats:
        stats_dict[metric_name] = {'avg': avg_val, 'sum': sum_val}

    METRIC_GUIDANCE = {
        'sleep_score': ['睡眠得分', 'avg', [60, 75, 100],
            '你的"恢复"质量。低于 70 会严重影响"脑力"能量。'],
        'sleep_total_min': ['总睡眠', 'avg', [390, 450, 600],
            f'你的"体能"基础。({stats_dict.get("sleep_total_min", {}).get("avg", 0) / 60:.1f} 小时)'],
        'rhr_avg': ['静息心率 (RHR)', 'avg', [68, 63, 50],
            '你的"恢复"信号灯。越高说明身体压力越大。'],
        'workout_train_load': ['训练负荷', 'avg', [120, 90, 0],
            '你的"消耗"量。这个值极高，需要大量睡眠来平衡。'],
        'workout_anaerobic_min': ['无氧训练', 'sum', [60, 40, 0],
            '高强度"消耗"。你的无氧时间远超有氧。'],
        'stress_avg': ['压力水平', 'avg', [40, 30, 0],
            '你"内耗"的客观体现。'],
        'workout_aerobic_min': ['有氧训练', 'sum', [1, 30, 150],
            '中强度"消耗"。这是你计划中的弱项。'],
        'workout_extreme_min': ['极限训练', 'sum', [10, 5, 0],
            '极高"消耗"。'],
        'heart_rate_avg': ['全天平均心率', 'avg', [85, 80, 60],
            '你的总体"唤醒"水平，被训练和压力拉高了。'],
        'sleep_deep_min': ['深睡时长', 'avg', [90, 110, 180],
            '你的核心"体能"恢复。'],
        'steps_total': ['日均步数', 'avg', [3000, 5000, 10000],
            '你的基础"消耗"水平。'],
    }

    for key, guidance in METRIC_GUIDANCE.items():
        if key in stats_dict:
            label, type, thresholds, desc = guidance
            value = stats_dict[key][type]

            bar_str, color = _create_bar_and_color(value, thresholds)

            # 特殊处理：为睡眠时长添加 (xx 小时)
            value_str = f"{value:.2f}"
            if key == 'sleep_total_min' and value > 0:
                value_str = f"{value:.2f} ({(value / 60):.1f} 小时)"

            # 格式化输出:
            # - 睡眠得分 (avg)     [██████░░░░] 60.44
            #   └ 你的"恢复"质量...

            # 使用 ljust 确保标签和数值对齐
            label_str = f"- {label} ({type})".ljust(22)
            value_str_aligned = value_str.ljust(20)

            click.echo(
                label_str +
                click.style(f"[{bar_str}] ", fg=color, bold=True) +
                value_str_aligned
            )
            click.echo(f"  └ {desc}")

    # --- 升级结束 ---

# --- 升级：提取数据逻辑供 API 使用 ---
def get_weekly_report_data(conn):
    """
    获取周报数据，返回字典格式。
    """
    c = conn.cursor()
    today = datetime.now()
    last_week = today - timedelta(days=7)

    # 1. 优先级分组统计
    c.execute("""
        SELECT
            CASE g.priority_level
                WHEN 1 THEN 'P1-High Priority'
                WHEN 2 THEN 'P2-Medium Priority'
                WHEN 3 THEN 'P3-Low Priority'
                ELSE 'Unassigned'
            END as priority_group,
            SUM(e.duration_minutes)
        FROM events e
        LEFT JOIN goals g ON e.goal_id = g.goal_id
        WHERE e.timestamp_start >= ?
        GROUP BY priority_group
        ORDER BY priority_group
    """, (last_week,))
    raw_goal_stats = c.fetchall()
    
    goal_stats = []
    total_duration = 0
    if raw_goal_stats:
        total_duration = sum(stat[1] for stat in raw_goal_stats if stat[1])
        for stat in raw_goal_stats:
            goal_stats.append({
                'group': stat[0],
                'minutes': stat[1],
                'hours': stat[1] / 60.0 if stat[1] else 0
            })

    # 2. 能量状态分布
    c.execute("""
        SELECT key_state, COUNT(*) FROM events
        WHERE timestamp_start >= ? GROUP BY key_state
    """, (last_week,))
    raw_state_stats = c.fetchall()
    
    state_stats = []
    if raw_state_stats:
        total_events = sum(stat[1] for stat in raw_state_stats)
        for stat in raw_state_stats:
            state_stats.append({
                'state': stat[0],
                'count': stat[1],
                'percentage': (stat[1] / total_events * 100) if total_events > 0 else 0
            })

    # 3. 洞察
    insights = {
        'internal_friction': [],
        'abundance': [],
        'consumption': []
    }
    
    c.execute("""
        SELECT activity, SUM(duration_minutes) FROM events
        WHERE key_state = 'Internal friction' AND timestamp_start >= ?
        GROUP BY activity ORDER BY SUM(duration_minutes) DESC LIMIT 3
    """, (last_week,))
    for row in c.fetchall():
        insights['internal_friction'].append({'activity': row[0], 'value': row[1]})

    c.execute("""
        SELECT activity, COUNT(*) as count FROM events
        WHERE key_state = 'Abundance' AND timestamp_start >= ?
        GROUP BY activity ORDER BY count DESC LIMIT 3
    """, (last_week,))
    for row in c.fetchall():
        insights['abundance'].append({'activity': row[0], 'value': row[1]})

    c.execute("""
        SELECT activity, AVG(duration_minutes) FROM events
        WHERE key_state = 'Consumption' AND timestamp_start >= ?
        GROUP BY activity ORDER BY AVG(duration_minutes) DESC LIMIT 3
    """, (last_week,))
    for row in c.fetchall():
        insights['consumption'].append({'activity': row[0], 'value': row[1]})

    # 4. 健康统计
    c.execute("""
        SELECT metric_type, AVG(value_numeric), SUM(value_numeric)
        FROM health_metrics
        WHERE timestamp >= ? AND value_numeric > 0
        GROUP BY metric_type
    """, (last_week,))
    raw_health_stats = c.fetchall()
    health_stats = []
    for row in raw_health_stats:
        health_stats.append({
            'metric': row[0],
            'avg': row[1],
            'sum': row[2]
        })

    return {
        'total_duration_hours': total_duration / 60.0,
        'goal_stats': goal_stats,
        'state_stats': state_stats,
        'insights': insights,
        'health_stats': health_stats
    }

def get_daily_plan_data(conn):
    """
    获取每日计划数据，返回字典格式。
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    
    data = {
        'budget': {},
        'plan': [],
        'recommendations': {},
        'error': None
    }

    try:
        today_budget = get_daily_energy_budget(conn, reference_date=yesterday)
        assessment = get_energy_assessment(conn, reference_date=yesterday)
        
        data['budget'] = {
            'total': today_budget,
            'sleep_hours': assessment.get('sleep_hours', 0),
            'rhr': assessment.get('latest_rhr', 0),
            'rhr_baseline': assessment.get('rhr_baseline', 0),
            'stress': assessment.get('latest_stress', 0)
        }
    except Exception as e:
        data['error'] = f"无法评估能量数据: {str(e)}"
        return data

    # 获取任务
    active_goals = database.get_active_goals(conn)
    if not active_goals:
        data['error'] = "没有活跃目标"
        return data
        
    p1_goals = [g for g in active_goals if g[2] == 1 and g[3] < 0]
    recovery_tasks = [g for g in active_goals if g[3] > 0]
    
    # 排序：恢复性任务优先，然后是P1消耗性任务
    recommended_actions = sorted(p1_goals + recovery_tasks, key=lambda x: x[3], reverse=True)
    
    remaining_budget = today_budget
    action_count = 0
    
    for goal in recommended_actions:
        goal_id, goal_name, priority, energy_cost = goal
        
        if remaining_budget + energy_cost < 0 and energy_cost < 0:
            continue 

        action_count += 1
        remaining_budget += energy_cost
        
        data['plan'].append({
            'order': action_count,
            'goal': goal_name,
            'priority': priority,
            'cost': energy_cost,
            'remaining_budget': remaining_budget
        })

    data['remaining_budget_final'] = remaining_budget
    
    # 推荐
    data['recommendations']['sleep'] = recommender.get_sleep_recommendation(conn)
    data['recommendations']['exercise'] = recommender.get_exercise_recommendation(conn)
    
    return data

@click.command()
def report():
    """Generates a weekly report."""
    conn = database.create_connection()
    data = get_weekly_report_data(conn)
    conn.close()

    click.echo("--- Weekly Report (Last 7 Days) ---")

    # 打印优先级报告
    if data['goal_stats']:
        click.echo(f"\nTotal time invested: {data['total_duration_hours']:.2f} hours")
        for stat in data['goal_stats']:
            name = stat['group']
            hours = stat['hours']
            if name == 'P1-High Priority':
                click.echo(click.style(f"- {name}: {hours:.2f} hours", fg="green", bold=True))
            elif name == 'P3-Low Priority':
                click.echo(click.style(f"- {name}: {hours:.2f} hours", fg="yellow", bold=True))
            else:
                click.echo(f"- {name}: {hours:.2f} hours")

    # 打印状态分布
    if data['state_stats']:
        click.echo("\nEnergy State Distribution (Subjective):")
        for stat in data['state_stats']:
            click.echo(f"- {stat['state']}: {stat['percentage']:.2f}%")

    # 打印健康分析 (复用现有函数，需要转换格式)
    if data['health_stats']:
        # 转换回 tuple list 供 print_health_analysis 使用
        health_stats_tuple = [(d['metric'], d['avg'], d['sum']) for d in data['health_stats']]
        print_health_analysis(health_stats_tuple)

    # 打印洞察
    insights = data['insights']
    if any(insights.values()):
        click.echo("\nStrategic Insights (Top 3):")
        if insights['internal_friction']:
            click.echo("- [Counteracting Internal Friction]: Your biggest sources:")
            for item in insights['internal_friction']:
                click.echo(f"  - '{item['activity']}', consuming {item['value']} minutes.")

        if insights['abundance']:
            click.echo("- [Discovering Abundance]: You feel most abundant after:")
            for item in insights['abundance']:
                click.echo(f"  - '{item['activity']}'.")

        if insights['consumption']:
            click.echo("- [Optimizing Consumption]: The activities leading to consumption are:")
            for item in insights['consumption']:
                click.echo(f"  - '{item['activity']}' after an average of {item['value']:.2f} minutes.")

@click.command()
def plan():
    """
    分析你过去的数据，为今天推荐一个最优的任务执行顺序。
    """
    conn = database.create_connection()
    data = get_daily_plan_data(conn)
    conn.close()
    
    if data.get('error'):
        click.echo(data['error'])
        return

    # 1. 获取能量预算
    click.echo(click.style("--- 你的今日能量预算 ---", bold=True))
    budget = data['budget']
    click.echo(click.style(f"--- 今日总预算: {budget['total']} 点 ---", bold=True, fg="green"))
    click.echo(f"(基于昨日数据: 睡眠 {budget['sleep_hours']:.1f} 小时, 静息心率 {budget['rhr']:.0f} (基线 {budget['rhr_baseline']:.0f}), 压力 {budget['stress']:.0f})")

    # 3. 输出新的行动计划
    click.echo(click.style("\n--- 推荐的行动计划 (P1 优先) ---", bold=True))
    
    if not data['plan']:
        click.echo("你的P1任务所需能量超过了你今天的预算。")
        click.echo("建议先从 '恢复' 型任务开始，或将大的P1任务分解为更小的步骤。")
    else:
        for item in data['plan']:
            cost_str = f"成本: {item['cost']}" if item['cost'] < 0 else f"收益: +{item['cost']}"
            click.echo(f"{item['order']}. [P{item['priority']}] {item['goal']} ({cost_str} 点)")
            click.echo(f"   剩余预算: {item['remaining_budget']} 点")

    click.echo(f"\n你还有 {data['remaining_budget_final']} 点能量预算可用于 P2/P3 任务或应对突发'内耗'。")

    # 4. 提供健康建议
    click.echo(click.style("\n--- 智能健康建议 ---", bold=True, fg="blue"))
    click.echo(click.style(f"睡眠: {data['recommendations']['sleep']}", fg="cyan"))
    click.echo(click.style(f"运动: {data['recommendations']['exercise']}", fg="cyan"))


# --- START: New 'journal' command ---
# (将此代码块添加到 analysis.py 的末尾)

# (替换 analysis.py 中的旧 journal 函数)
@click.command()
@click.option('--days', default=3, type=int, help='要查看的过去天数 (默认: 3)')
def journal(days):
    """
    显示每日日记，结合客观健康指标、主观事件日志和能量预算汇总。
    """
    conn = database.create_connection()
    c = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    click.echo(f"--- 综合每日日记 (Last {days} Day(s)) ---")

    # (SQL 查询 1: 获取主观事件 - 已包含 energy_cost)
    c.execute("""
              SELECT e.timestamp_start, e.activity, e.duration_minutes, e.key_state, 
                     g.goal_name, g.priority_level, g.energy_cost
              FROM events e
                       LEFT JOIN goals g ON e.goal_id = g.goal_id
              WHERE DATE (e.timestamp_start) >= ?
              ORDER BY e.timestamp_start DESC
              """, (start_date,))
    all_events = c.fetchall()

    events_by_date = {}
    for event in all_events:
        event_date = datetime.fromisoformat(event[0]).date()
        if event_date not in events_by_date:
            events_by_date[event_date] = []
        events_by_date[event_date].insert(0, event) # 按时间正序

    # (SQL 查询 2: 获取客观指标)
    c.execute("""
              SELECT timestamp, metric_type, value_numeric
              FROM health_metrics
              WHERE DATE (timestamp) >= ? AND value_numeric > 0
              ORDER BY timestamp
              """, (start_date,))
    all_metrics = c.fetchall()

    metrics_by_date = {}
    for metric in all_metrics:
        metric_date = datetime.fromisoformat(metric[0]).date()
        metric_type = metric[1]
        metric_value = metric[2]
        if metric_date not in metrics_by_date:
            metrics_by_date[metric_date] = {}
        metrics_by_date[metric_date][metric_type] = metric_value

    all_dates = sorted(list(set(events_by_date.keys()) | set(metrics_by_date.keys())), reverse=True)

    if not all_dates:
        click.echo("在指定日期内没有找到任何客观或主观数据。")
        conn.close()
        return

    # --- 升级: 循环并计算预算 ---
    for date in all_dates:
        click.echo(click.style(f"\n--- {date.strftime('%Y-%m-%d, %A')} ---", bold=True, fg="blue"))

        # --- 升级 (1): 调用每日预算 ---
        # (这会根据当天的客观数据计算初始预算)
        initial_budget = get_daily_energy_budget(conn, reference_date=date)

        # (客观指标部分保持不变)
        click.echo(click.style("  Objective Health (来自手环):", bold=True))
        day_metrics = metrics_by_date.get(date)
        if day_metrics:
            # (省略了内部的打印逻辑，与您现有的代码相同)
            key_metrics_map = {
                'sleep_score': '睡眠得分', 'sleep_total_min': '睡眠时长',
                'rhr_avg': '静息心率(RHR)', 'stress_avg': '平均压力',
                'steps_total': '总步数'
            }
            metrics_found_count = 0
            for key, label in key_metrics_map.items():
                if key in day_metrics:
                    value = day_metrics[key]
                    if key == 'sleep_total_min':
                        click.echo(f"    - {label}: {value:.0f} 分钟 ({value / 60:.1f} 小时)")
                    elif key == 'rhr_avg' or key == 'stress_avg':
                        click.echo(f"    - {label}: {value:.0f}")
                    elif key == 'sleep_score':
                        click.echo(click.style(f"    - {label}: {value:.0f}",
                                               fg=("green" if value >= 75 else "yellow" if value >= 60 else "red")))
                    else:
                        click.echo(f"    - {label}: {value:.0f}")
                    metrics_found_count += 1
            if metrics_found_count == 0:
                click.echo("    (当天未导入关键的摘要指标。)")
        else:
            click.echo("    (当天没有导入客观健康数据。)")

        click.echo(click.style("\n  Subjective Log (您的记录):", bold=True))
        day_events = events_by_date.get(date)
        total_daily_cost = 0 # 跟踪总消耗
        
        if day_events:
            total_duration = 0
            for event in day_events:
                # (日志打印逻辑与您现有的代码相同)
                timestamp_str, activity, duration, key_state, goal_name, priority, energy_cost = event
                timestamp = datetime.fromisoformat(timestamp_str)
                time_str = timestamp.strftime('%H:%M')
                goal_str = ""
                if goal_name:
                    cost_str = ""
                    if energy_cost is not None:
                        cost_str = f"Cost: {energy_cost}"
                        if energy_cost < 0: cost_str = click.style(cost_str, fg="red")
                        elif energy_cost > 0: cost_str = click.style(cost_str, fg="green")
                        total_daily_cost += energy_cost # 累加
                    goal_str = f" (目标: {goal_name} [P{priority}], {cost_str})"

                state_color = "white"
                if key_state == "Internal friction": state_color = "yellow"
                elif key_state == "Consumption": state_color = "cyan"
                elif key_state == "Growth" or key_state == "Abundance": state_color = "green"
                click.echo(
                    f"    [{time_str}] {activity} ({duration} 分钟) - " +
                    click.style(f"{key_state}", fg=state_color) +
                    f"{goal_str}"
                )
                total_duration += duration
            click.echo(f"  └ 记录总时长: {total_duration / 60:.2f} 小时")
        else:
            click.echo("    (当天没有记录主观事件。)")
        
        # --- 升级 (2): 打印完整的预算摘要 ---
        click.echo(click.style("\n  Daily Energy Summary:", bold=True))
        
        # 计算剩余净值
        # 注意: total_daily_cost 本身是负数 (如 -31), 所以我们用加法
        remaining_budget = initial_budget + total_daily_cost

        # 设置剩余净值的颜色
        remaining_color = "white"
        if remaining_budget < 0: remaining_color = "red"
        elif remaining_budget > 10: remaining_color = "green" # 如果剩余很多，也是绿色

        click.echo(click.style(f"    初始预算 (基于客观数据): {initial_budget} 点", fg="blue"))
        click.echo(click.style(f"    主观消耗/恢复 (来自日志): {total_daily_cost} 点", fg=("red" if total_daily_cost < 0 else "green")))
        click.echo(click.style(f"    ---------------------------------", bold=True))
        click.echo(click.style(f"    估算剩余能量净值: {remaining_budget} 点", fg=remaining_color, bold=True))
        

    conn.close()

# --- END: New 'journal' command ---
# --- START: New 'trend' command (FIXED) ---
# (将此代码块添加到 analysis.py 的末尾, 替换旧的 'trend' 函数)

@click.command()
@click.option('--days', default=7, type=int, help='要查看的过去天数 (默认: 7)')
def trend(days):
    """
    以表格形式显示客观指标和主观日志的每日趋势。
    """
    conn = database.create_connection()
    c = conn.cursor()

    # 1. 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    click.echo(f"--- 能量趋势对比表 (Last {days} Days) ---")

    # 2. 准备一个字典来按天存储所有数据
    all_data = {}

    # 3. [SQL 查询 1] 获取客观健康指标 (使用 SQL PIVOT)
    c.execute("""
              SELECT
                  DATE (timestamp) as day, MAX (CASE WHEN metric_type = 'sleep_score' THEN value_numeric ELSE NULL END) as sleep_score, MAX (CASE WHEN metric_type = 'sleep_total_min' THEN value_numeric ELSE NULL END) as sleep_total, MAX (CASE WHEN metric_type = 'rhr_avg' THEN value_numeric ELSE NULL END) as rhr, MAX (CASE WHEN metric_type = 'stress_avg' THEN value_numeric ELSE NULL END) as stress
              FROM health_metrics
              WHERE DATE (timestamp) >= ? AND DATE (timestamp) <= ?
              GROUP BY day
              """, (start_date, end_date))

    obj_metrics = c.fetchall()

    # 填充 all_data 字典
    for row in obj_metrics:
        day, sleep_score, sleep_total, rhr, stress = row
        all_data[day] = {
            'sleep_score': sleep_score,
            'sleep_total': sleep_total,
            'rhr': rhr,
            'stress': stress
        }

    # 4. [SQL 查询 2] 获取主观日志聚合 (按小时)
    c.execute("""
              SELECT
                  DATE (timestamp_start) as day, key_state, SUM (duration_minutes) / 60.0 as total_hours
              FROM events
              WHERE DATE (timestamp_start) >= ? AND DATE (timestamp_start) <= ?
              GROUP BY day, key_state
              """, (start_date, end_date))

    subj_metrics = c.fetchall()

    # 填充 all_data 字典
    for row in subj_metrics:
        day, key_state, total_hours = row
        if day not in all_data:
            all_data[day] = {}
        all_data[day][key_state] = total_hours

    conn.close()

    # 5. 打印表格
    # 打印表头
    header = (
        f"{'Date':<11} | "
        f"{'Sleep(S)':>8} "
        f"{'Sleep(H)':>8} "
        f"{'RHR':>5} "
        f"{'Stress':>6} | "
        f"{'Friction(H)':>11} "
        f"{'Growth(H)':>10} "
        f"{'Abund(H)':>8} "
        f"{'Consump(H)':>10}"
    )
    click.echo(click.style(header, bold=True))
    click.echo(click.style("-" * len(header), bold=True))

    # 循环打印每一天的数据
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.isoformat()

        day_data = all_data.get(date_str, {})

        # --- FIX: 确保 None 值被转换为 0 ---
        # (旧: day_data.get('key', 0) -> 新: day_data.get('key') or 0)
        # 准备客观数据
        s_score = day_data.get('sleep_score') or 0
        s_total = (day_data.get('sleep_total') or 0) / 60.0
        rhr = day_data.get('rhr') or 0
        stress = day_data.get('stress') or 0
        # --- END FIX ---

        # 准备主观数据
        friction_h = day_data.get('Internal friction', 0)
        growth_h = day_data.get('Growth', 0)
        abund_h = day_data.get('Abundance', 0)
        consump_h = day_data.get('Consumption', 0)

        # 格式化输出
        row_str = (
            f"{date_str:<11} | "
            f"{s_score: >8.0f} "
            f"{s_total: >8.1f} "
            f"{rhr: >5.0f} "
            f"{stress: >6.0f} | "
            f"{friction_h: >11.1f} "
            f"{growth_h: >10.1f} "
            f"{abund_h: >8.1f} "
            f"{consump_h: >10.1f}"
        )

        # 为关键指标添加颜色
        if s_score > 0 and s_score < 70:
            click.echo(click.style(row_str, fg="yellow"))
        elif rhr > 0 and rhr > (day_data.get('rhr_baseline', 65) + 4):  # (假设基线为65)
            click.echo(click.style(row_str, fg="red"))
        elif friction_h > 2:
            click.echo(click.style(row_str, fg="cyan"))
        else:
            click.echo(row_str)

# --- END: New 'trend' command (FIXED) ---
# --- START: New 'plot' command ---
# (将此代码块添加到 analysis.py 的末尾)

@click.command()
@click.option('--metric',
              default='sleep_score',
              type=click.Choice(['sleep_score', 'stress_avg', 'rhr_avg', 'steps_total'], case_sensitive=False),
              help='您想要绘制的健康指标。')
@click.option('--days', default=30, type=int, help='您想要查看的过去天数。')
@click.option('--output', default=None, help='输出图像的文件名 (例如: my_plot.png)')
def plot(metric, days, output):
    """
    生成一个健康指标的时间序列折线图并将其保存为文件。

    此命令不会“显示”图表，而是将其保存为一个PNG文件。
    """
    click.echo(f"正在为 '{metric}' 生成过去 {days} 天的图表...")

    conn = database.create_connection()
    c = conn.cursor()

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    # 1. 从数据库获取数据
    # (您在 importer.py 中定义的指标名称)
    c.execute("""
              SELECT
                  DATE (timestamp) as day, value_numeric
              FROM health_metrics
              WHERE DATE (timestamp) >= ?
                AND DATE (timestamp) <= ?
                AND metric_type = ?
              ORDER BY day
              """, (start_date, end_date, metric))

    data = c.fetchall()

    if not data:
        click.echo(click.style(f"错误: 在过去 {days} 天内未找到 '{metric}' 的数据。", fg="red"))
        conn.close()
        return

    # 2. 将数据转换为 Pandas DataFrame (Seaborn 最擅长处理)
    df = pd.DataFrame(data, columns=['date', 'value'])
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'])

    # 3. 创建图表 (使用 plt.figure 来确保图表被正确创建)
    plt.figure(figsize=(12, 7))  # 设置图表大小
    sns.set_theme(style="whitegrid")

    # 绘制数据折线
    g = sns.lineplot(data=df, x='date', y='value', marker='o', label=f'每日 {metric}')

    # 绘制7天滚动平均线，让趋势更清晰
    df['7-day avg'] = df['value'].rolling(window=7, min_periods=1).mean()
    sns.lineplot(data=df, x='date', y='7-day avg', color='red', linestyle='--', label='7天滚动平均')

    g.set_title(f"每日 {metric.replace('_', ' ').title()} (过去 {days} 天)", fontsize=16)
    g.set_xlabel("日期", fontsize=12)
    g.set_ylabel(metric.replace('_', ' ').title(), fontsize=12)

    # 格式化X轴的日期，使其更易读
    date_form = DateFormatter("%m-%d")
    g.xaxis.set_major_formatter(date_form)
    plt.xticks(rotation=45)

    plt.legend()
    plt.tight_layout()  # 自动调整布局，防止标签被截断

    # 4. 保存图表到文件 (替换 plt.show())
    if not output:
        output_filename = f"daily_{metric}_trend.png"
    else:
        output_filename = output

    try:
        plt.savefig(output_filename)  # <-- 关键步骤
        conn.close()
        click.echo(click.style(f"\n成功! 图表已保存至: {output_filename}", fg="green"))
    except Exception as e:
        conn.close()
        click.echo(click.style(f"\n保存图表时出错: {e}", fg="red"))

    # 释放内存
    plt.clf()

# --- END: New 'plot' command ---