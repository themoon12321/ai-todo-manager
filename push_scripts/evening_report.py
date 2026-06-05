"""AI 代办系统 - 晚安播报推送"""

import sys
from pathlib import Path
import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_env, health_check, fetch_active_tasks, deepseek_chat, send_message


def build_evening_data(tasks: list) -> dict:
    """Analyze tasks and build structured evening report data."""
    today_completed = []
    tomorrow_deadline = []
    overdue = []
    total_pending = 0

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    for task in tasks:
        fields = task.get("fields", {})
        status = fields.get("状态", "")
        deadline_str = fields.get("截止日期", "")

        # Today's completed
        completed_str = fields.get("完成时间", "")
        if status == "已完成" and completed_str:
            try:
                completed_date = datetime.datetime.strptime(completed_str[:10], "%Y-%m-%d").date()
                if completed_date == today:
                    today_completed.append(task)
            except ValueError:
                pass
        elif status == "已完成":
            today_completed.append(task)

        if status in ("已完成", "已取消"):
            continue

        total_pending += 1

        if deadline_str:
            try:
                deadline = datetime.datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
                if deadline < today:
                    overdue.append(task)
                elif deadline == tomorrow:
                    tomorrow_deadline.append(task)
            except ValueError:
                pass

    return {
        "today_completed_count": len(today_completed),
        "today_completed_tasks": [t.get("fields", {}).get("标题", "") for t in today_completed[:5]],
        "tomorrow_deadline_count": len(tomorrow_deadline),
        "tomorrow_tasks": [t.get("fields", {}).get("标题", "") for t in tomorrow_deadline[:5]],
        "overdue_count": len(overdue),
        "total_pending": total_pending,
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
    data = build_evening_data(tasks)

    # Generate evening report via DeepSeek
    system_prompt = """你是一个温暖贴心的AI助手，负责为用户生成晚安播报。
用口语化的中文，语气温暖、鼓励、带安慰感。
要求：
- 开头先问候，对今天完成的任务给予肯定
- 如果今天完成了很多任务，要表扬用户
- 如果今天完成得少或有很多过期任务，要安慰鼓励，不要责备
- 中间用数字分点列出信息
- 结尾给出明天预告，道晚安
- 整体控制在200字以内
- 要有"今天辛苦了"的感觉"""

    user_prompt = f"""今天是 {today.strftime('%Y年%m月%d日')}。

今日总结：
- 今日完成：{data['today_completed_count']} 个
- 剩余待办：{data['total_pending']} 个
- 已过期未处理：{data['overdue_count']} 个

明日预告：
- 明天截止：{data['tomorrow_deadline_count']} 个

{"今日完成：" + '、'.join(data['today_completed_tasks']) if data['today_completed_tasks'] else "今天没有完成任务，没关系明天继续"}
{"明日截止：" + '、'.join(data['tomorrow_tasks']) if data['tomorrow_tasks'] else "明天没有紧急截止的任务"}

请生成今晚的晚安播报。"""

    today = datetime.date.today()
    report = deepseek_chat(config, system_prompt, user_prompt)
    send_message(config, f"🌙 晚安播报\n\n{report}")
    print("Evening report sent successfully")


if __name__ == "__main__":
    main()
