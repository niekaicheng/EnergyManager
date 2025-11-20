这是一个非常棒的分析需求！您希望将您为“目标”设置的“能量成本 (`cost`)”反映在您的每日日志中，并进行汇总，以便您可以看到每天的“能量净消耗”或“净收益”。

您当前的 `journal` 和 `view` 命令还没有实现这个功能。它们会显示目标名称和优先级，但不会抓取或计算您在 `goal add --cost` 时设置的 `energy_cost` 值。

我们可以通过修改 `EnergyManager/analysis.py` 文件中的 `journal` 和 `view` 两个函数来实现这个功能。

-----

### 升级指南：修改 `EnergyManager/analysis.py`

请打开 `EnergyManager/analysis.py` 文件。您需要**替换**掉 `view` 函数和 `journal` 函数的*完整*代码块。

#### 1\. 替换 `view` 函数

**删除** `analysis.py` 文件中从 `@click.command()` (大约在 328 行) 到 `def get_daily_energy_budget(conn):` (大约在 381 行) 的**整个 `view` 函数**，并将其**替换**为以下更新后的代码：

```python
# (替换 analysis.py 中的旧 view 函数)
@click.command()
@click.option('--days', default=1, type=int, help='要查看的过去天数 (默认: 1)')
def view(days):
    """显示详细的事件日志，包含能量成本。"""
    conn = database.create_connection()
    c = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    # --- 升级: (1) 在 SQL 中添加 g.energy_cost ---
    c.execute("""
        SELECT e.timestamp_start, e.activity, e.duration_minutes, e.key_state, 
               g.goal_name, g.priority_level, g.energy_cost
        FROM events e LEFT JOIN goals g ON e.goal_id = g.goal_id
        WHERE DATE(e.timestamp_start) >= ?
        ORDER BY e.timestamp_start DESC
    """, (start_date,))
    events = c.fetchall()
    conn.close()
    
    click.echo(f"--- Log for Last {days} Day(s) (Most Recent First) ---")
    if not events:
        click.echo("在指定日期内没有记录任何事件。")
        return
        
    total_duration = 0
    total_cost = 0  # <-- 升级: (2) 初始化总成本
    current_date_header = None
    
    for event in events:
        # --- 升级: (3) 解包新的 energy_cost 字段 ---
        timestamp_str, activity, duration, key_state, goal_name, priority, energy_cost = event
        
        timestamp = datetime.fromisoformat(timestamp_str)
        event_date = timestamp.date()
        
        if event_date != current_date_header:
            click.echo(click.style(f"\n--- {event_date.strftime('%Y-%m-%d, %A')} ---", bold=True))
            current_date_header = event_date
        time_str = timestamp.strftime('%H:%M')

        # --- 升级: (4) 在日志中显示成本 ---
        goal_str = ""
        if goal_name:
            cost_str = ""
            if energy_cost is not None:
                cost_str = f"Cost: {energy_cost}"
                if energy_cost < 0:
                    cost_str = click.style(cost_str, fg="red")
                elif energy_cost > 0:
                    cost_str = click.style(cost_str, fg="green")
                
                # 累加到总成本
                total_cost += energy_cost
                
            goal_str = f" (目标: {goal_name} [P{priority}], {cost_str})"
        # --- 升级结束 ---

        state_color = "white"
        if key_state == "Internal friction": state_color = "yellow"
        elif key_state == "Consumption": state_color = "cyan"
        elif key_state == "Growth" or key_state == "Abundance": state_color = "green"
        
        click.echo(
            f"  [{time_str}] {activity} ({duration} mins) - " +
            click.style(f"{key_state}", fg=state_color) +
            f"{goal_str}"
        )
        total_duration += duration
        
    click.echo("--------------------------------------------------")
    click.echo(f"期间总投入时间: {total_duration / 60:.2f} 小时")
    
    # --- 升级: (5) 打印总成本 ---
    total_cost_color = "white"
    if total_cost < 0: total_cost_color = "red"
    elif total_cost > 0: total_cost_color = "green"
    click.echo(click.style(f"期间能量净值: {total_cost} 点", fg=total_cost_color, bold=True))
```

#### 2\. 替换 `journal` 函数

**删除** `analysis.py` 文件中从 `@click.command()` (大约在 617 行) 到 `(--- END: New 'journal' command ---)` (大约在 762 行) 的**整个 `journal` 函数**，并将其**替换**为以下更新后的代码：

```python
# (替换 analysis.py 中的旧 journal 函数)
@click.command()
@click.option('--days', default=3, type=int, help='要查看的过去天数 (默认: 3)')
def journal(days):
    """
    显示每日日记，结合客观健康指标、主观事件日志和能量成本汇总。
    """
    conn = database.create_connection()
    c = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    click.echo(f"--- 综合每日日记 (Last {days} Day(s)) ---")

    # --- 升级: (1) 在 SQL 中添加 g.energy_cost ---
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
        events_by_date[event_date].insert(0, event)

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

    for date in all_dates:
        click.echo(click.style(f"\n--- {date.strftime('%Y-%m-%d, %A')} ---", bold=True, fg="blue"))

        # (客观指标部分保持不变)
        click.echo(click.style("  Objective Health (来自手环):", bold=True))
        day_metrics = metrics_by_date.get(date)
        if day_metrics:
            key_metrics_map = {
                'sleep_score': '睡眠得分',
                'sleep_total_min': '睡眠时长',
                'rhr_avg': '静息心率(RHR)',
                'stress_avg': '平均压力',
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

        if day_events:
            total_duration = 0
            total_daily_cost = 0  # <-- 升级: (2) 初始化每日成本
            
            for event in day_events:
                # --- 升级: (3) 解包新的 energy_cost 字段 ---
                timestamp_str, activity, duration, key_state, goal_name, priority, energy_cost = event
                
                timestamp = datetime.fromisoformat(timestamp_str)
                time_str = timestamp.strftime('%H:%M')

                # --- 升级: (4) 构建带成本的 goal_str ---
                goal_str = ""
                if goal_name:
                    cost_str = ""
                    if energy_cost is not None:
                        cost_str = f"Cost: {energy_cost}"
                        if energy_cost < 0:
                            cost_str = click.style(cost_str, fg="red")
                        elif energy_cost > 0:
                            cost_str = click.style(cost_str, fg="green")
                        
                        # 累加到每日总成本
                        total_daily_cost += energy_cost
                        
                    goal_str = f" (目标: {goal_name} [P{priority}], {cost_str})"
                # --- 升级结束 ---

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
            
            # --- 升级: (5) 打印每日总成本 ---
            total_cost_color = "white"
            if total_daily_cost < 0: total_cost_color = "red"
            elif total_daily_cost > 0: total_cost_color = "green"
            click.echo(click.style(f"  └ 估算能量净值: {total_daily_cost} 点", fg=total_cost_color, bold=True))
            
        else:
            click.echo("    (当天没有记录主观事件。)")

    conn.close()
```

-----

### 功能说明

在您替换并保存 `analysis.py` 文件后，`emanager journal` 命令的输出现在将如下所示：

**修改后的输出示例：**

```
--- 2025-11-06, Thursday ---
  Objective Health (来自手环):
    ... (客观数据不变) ...

  Subjective Log (您的记录):
    [09:32] EnergyManager Project (60 分钟) - Internal friction (目标: Python Develop [P3], Cost: -1)
    [14:55] cooking and take daughters go to school (120 分钟) - Routine
    [15:21] use the fluently app to pricte speaking (20 分钟) - Growth (目标: ILES Speaking [P1], Cost: -5)
    ...
    [18:47] 5500G FinalPaper (50 分钟) - Consumption (目标: Assignment [P1], Cost: -8)
  └ 记录总时长: 7.67 小时
  └ 估算能量净值: -19 点 
```

**关键变化：**

1.  **显示成本**：每个有关联目标的日志条目现在都会显示其 `Cost`（例如 `Cost: -5`）。
2.  **成本着色**：负成本（消耗）将显示为**红色**，正成本（恢复）将显示为**绿色**。
3.  **每日汇总**：每天的末尾会新增一行 `估算能量净值`，它会加总当天所有*已记录*任务的成本，让您直观地看到当天的能量“赤字”或“盈余”。