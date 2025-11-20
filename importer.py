# importer.py
import click
import database
import csv
import json
from datetime import datetime

def parse_aggregated_data(filepath):
    """
    [cite_start]解析 hlth_center_aggregated_fitness_data.csv  [cite: 70, 312, 377-655, 713, 700, 708, 720]
    """
    metrics = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Tag') != 'daily_report':
                continue
            try:
                ts = datetime.fromtimestamp(int(row['Time']))
                key = row['Key']
                value_json = json.loads(row['Value'])

                if key == 'sleep':
                    metrics.append((ts, 'sleep_total_min', value_json.get('total_duration'), row['Value']))
                    metrics.append((ts, 'sleep_deep_min', value_json.get('sleep_deep_duration'), row['Value']))
                    metrics.append((ts, 'sleep_score', value_json.get('sleep_score'), row['Value']))
                elif key == 'steps':
                    metrics.append((ts, 'steps_total', value_json.get('steps'), row['Value']))
                elif key == 'calories':
                    metrics.append((ts, 'calories_total', value_json.get('calories'), row['Value']))
                elif key == 'stress':
                    metrics.append((ts, 'stress_avg', value_json.get('avg_stress'), row['Value']))
                elif key == 'heart_rate':
                    metrics.append((ts, 'rhr_avg', value_json.get('avg_rhr'), row['Value']))
                    metrics.append((ts, 'heart_rate_avg', value_json.get('avg_hr'), row['Value']))
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    return metrics

def parse_sport_records(filepath):
    """
    [cite_start]解析 hlth_center_sport_record.csv  [cite: 71, 311, 378-381, 711, 750, 753]
    """
    metrics = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.fromtimestamp(int(row['Time']))
                key = row['Key']
                value_json = json.loads(row['Value'])
                
                duration_min = value_json.get('duration', 0) / 60.0
                
                # --- 新增：提取心率区间数据 ---
                aerobic_min = value_json.get('hrm_aerobic_duration', 0) / 60.0
                anaerobic_min = value_json.get('hrm_anaerobic_duration', 0) / 60.0
                extreme_min = value_json.get('hrm_extreme_duration', 0) / 60.0
                # --- 结束 ---
                
                metrics.append((ts, f'workout_duration_min', duration_min, row['Value']))
                metrics.append((ts, f'workout_calories', value_json.get('calories'), row['Value']))
                metrics.append((ts, f'workout_avg_hrm', value_json.get('avg_hrm'), row['Value']))
                metrics.append((ts, f'workout_train_load', value_json.get('train_load'), row['Value']))
                
                # --- 新增：存入新指标 ---
                metrics.append((ts, f'workout_aerobic_min', aerobic_min, row['Value']))
                metrics.append((ts, f'workout_anaerobic_min', anaerobic_min, row['Value']))
                metrics.append((ts, f'workout_extreme_min', extreme_min, row['Value']))
                # --- 结束 ---
                
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    return metrics


@click.command("import")
@click.argument('filepath', type=click.Path(exists=True))
def import_data(filepath):
    """
    从导出的CSV文件 (如小米手环) 导入健康数据。
    """
    click.echo(f"正在从 {filepath} 导入数据...")
    metrics_data = []
    filename = filepath.split('/')[-1]

    if 'aggregated_fitness_data' in filename:
        click.echo("检测到 'Aggregated Fitness Data' (每日总结) ...")
        metrics_data = parse_aggregated_data(filepath)
    elif 'sport_record' in filename:
        click.echo("检测到 'Sport Record' (运动记录) ...")
        metrics_data = parse_sport_records(filepath)
    else:
        click.echo(f"错误: 不支持的文件。目前仅支持 '...aggregated...' 和 '...sport_record...' 文件。", err=True)
        return

    if not metrics_data:
        click.echo("没有解析到任何有效数据。")
        return

    conn = database.create_connection()
    # insert_health_metrics_batch 已经包含了 "INSERT OR IGNORE"
    database.insert_health_metrics_batch(conn, metrics_data)
    conn.close()
    
    click.echo(click.style(f"成功！导入了 {len(metrics_data)} 条健康记录。", fg="green"))