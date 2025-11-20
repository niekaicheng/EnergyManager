# constants.py
"""
集中存储关键状态 (Key State) 的定义。
"""

# 你的“状态表”，键(英文)用于数据库，值(中文)用于你的理解
KEY_STATE_CHOICES = {
    "Consumption": "消耗",  # 高强度、有产出后的疲惫
    "Internal friction": "内耗",  # 迷茫、空闲时的能量空转
    "Growth": "成长",        # 学习、掌握新技能
    "Abundance": "充沛",       # 锻炼、休息后精力旺盛
    "Routine": "常规"         # 日常事务，能量平稳
}

# 提取英文键列表，供 click.Choice 使用
CLI_STATE_CHOICES = list(KEY_STATE_CHOICES.keys())
