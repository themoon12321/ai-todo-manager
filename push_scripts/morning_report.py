"""AI 代办系统 - 早安播报推送"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_env, health_check, fetch_active_tasks, deepseek_chat, send_message


def build_morning_data(tasks: list) -> dict:
    """Analyze tasks and build structured morning report data."""
    today_deadline = []
    overdue = []
    no_deadline = []
    priority_counts = {"P0 🔥": 0, "P1 🔴": 0, "P2 🟡": 0, "P3 🟢": 0, "P4 ⚪": 0}
    total = 0

    import datetime
    today = datetime.date.today()

    for task in tasks:
        fields = task.get("fields", {})
        status = fields.get("状态", "")
        deadline_str = fields.get("截止日期", "")

        if status in ("已完成", "已取消"):
            continue

        total += 1
        priority = fields.get("优先级", "")
        if priority in priority_counts:
            priority_counts[priority] += 1

        if deadline_str:
            try:
                deadline = datetime.datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
                if deadline < today:
                    overdue.append(task)
                elif deadline == today:
                    today_deadline.append(task)
            except ValueError:
                no_deadline.append(task)
        else:
            no_deadline.append(task)

    return {
        "total_pending": total,
        "today_deadline_count": len(today_deadline),
        "overdue_count": len(overdue),
        "no_deadline_count": len(no_deadline),
        "priority_counts": priority_counts,
        "overdue_tasks": [t.get("fields", {}).get("标题", "") for t in overdue[:5]],
        "today_tasks": [t.get("fields", {}).get("标题", "") for t in today_deadline[:5]],
    }


def main():
    config = load_env()

    # Health check
    failures = health_check(config)
    if failures:
        alert = "⚠️ AI 代办健康检查失败：\n" + "\n".join(failures)
        send_message(config, alert)
        print("Health check failed, alert sent")
        return

    # Fetch tasks
    tasks = fetch_active_tasks(config)
    data = build_morning_data(tasks)

    # Generate morning report via DeepSeek
    system_prompt = """你是一个温暖贴心的AI助手，负责为用户生成早安播报。
用口语化的中文，语气根据时间带感情色彩。
要求：
- 开头先问候，根据数据调整语气（今天任务多就加油打气，少就轻松愉快）
- 中间用数字分点列出关键信息
- 结尾给出今日建议（优先做什么）
- 整体控制在200字以内
- 不要冷冰冰的数据堆砌，要有人情味"""

    user_prompt = f"""今天是 {__import__('datetime').date.today().strftime('%Y年%m月%d日')}。

今日任务概览：
- 待办任务总数：{data['total_pending']} 个
- 今日截止：{data['today_deadline_count']} 个
- 已过期：{data['overdue_count']} 个
- 无截止日期：{data['no_deadline_count']} 个

优先级分布：
{chr(10).join(f'  {k}: {v}个' for k, v in data['priority_counts'].items() if v > 0)}

{"今日截止任务：" + '、'.join(data['today_tasks']) if data['today_tasks'] else ""}
{"已过期任务：" + '、'.join(data['overdue_tasks']) if data['overdue_tasks'] else ""}

请生成今天的早安播报。"""

    report = deepseek_chat(config, system_prompt, user_prompt)
    send_message(config, f"🌅 早安播报\n\n{report}")
    print("Morning report sent successfully")


if __name__ == "__main__":
    main()
