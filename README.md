# Personal Energy Manager

This is a simple command-line application to help you track and manage your personal energy levels based on the concepts described in GEMINI.md.

## How to Use

1.  Run the application:

    ```bash
    python3 main.py
    ```

2.  The application will prompt you to enter the following information:

    *   Your current activity
    *   Your physical, mental, and emotional energy levels (on a scale of 1-10)
    *   Your current energy state (Consumption, Internal friction, Growth, or Abundance)

3.  The application will save your input to a file named `energy_log.json`.

## Future Improvements

*   Add data analysis and visualization features.
*   Provide personalized suggestions based on the user's energy patterns.
*   Create a more user-friendly interface (e.g., a web or mobile app).

[//]: # ('''命令,完整用法,解释)

[//]: # (初始化,python3 emanager.py init,创建或更新你的数据库 &#40;emanager.db&#41;。（在新系统或清理后首先运行）)

[//]: # (添加目标,"python3 emanager.py goal add ""新目标""",添加一个新的长期目标，如“雅思学习”。)

[//]: # (列出目标,python3 emanager.py goal list,显示所有活跃的目标及其 ID。)

[//]: # (归档目标,python3 emanager.py goal archive [目标ID],按 ID 归档一个已完成的目标（它不会被删除）。)

[//]: # (记录事件,python3 emanager.py log,（核心功能） 启动交互式提示，记录你的活动、P/M/E 分数和状态。完成后会自动触发“即时指导”。)

[//]: # (导入数据,python3 emanager.py import [文件路径],（核心功能） 导入你的小米 CSV 数据。例如 ... import ./mifitdata/...csv。)

[//]: # (获取计划,python3 emanager.py plan,（核心功能） 分析你的客观数据（睡眠/心率）和主观数据，为你推荐今天的学习和运动计划。)

[//]: # (查看周报,python3 emanager.py report,显示过去 7 天的总结报告，包含你的主观状态分布和客观健康指标（如心率、睡眠、有氧/无氧分钟数）。)

[//]: # (查看日志,python3 emanager.py view,显示今天的详细事件日志。)

[//]: # (,python3 emanager.py view --days 7,显示最近 7 天的详细事件日志，按天分组。)

[//]: # (开始追踪,"python3 emanager.py start ""活动名""",启动一个实时计时器。)

[//]: # (停止追踪,python3 emanager.py stop,停止计时器，并提醒你运行 log 来记录详情。)

[//]: # (''')
