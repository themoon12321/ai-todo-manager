"""AI 代办系统 - 晚安播报推送"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_env, health_check, fetch_active_tasks, deepseek_chat, send_message


def build_evening_context(tasks: list) -> str:
    """Build structured evening report data for DeepSeek prompt."""
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    completed_today = []
    todo = []
    in_progress = []
    overdue = []
    tomorrow_due = []

    for t in tasks:
        f = t.get("fields", {})
        status = f.get("状态", "")
        deadline_str = f.get("截止日期", "")
        completed_str = f.get("完成时间", "")

        task_info = {
            "title": f.get("标题", ""),
            "priority": f.get("优先级", ""),
            "deadline": deadline_str[:10] if deadline_str else None,
            "hours": f.get("预估时长"),
            "category": f.get("所属分类", ""),
            "status": status
        }

        # Check if completed today
        if status == "已完成" and completed_str:
            try:
                cd = datetime.datetime.strptime(completed_str[:10], "%Y-%m-%d").date()
                if cd == today:
                    completed_today.append(task_info)
                    continue
            except ValueError:
                pass

        if status == "已完成" or status == "已取消":
            continue

        if status == "进行中":
            in_progress.append(task_info)
        else:
            todo.append(task_info)

        if deadline_str:
            try:
                d = datetime.datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
                if d < today:
                    overdue.append(task_info)
                elif d == tomorrow:
                    tomorrow_due.append(task_info)
            except ValueError:
                pass

    # Stats
    total = len(tasks)
    done_count = len(completed_today)
    pending = total - done_count

    return f"""今天是 {today.strftime('%Y年%m月%d日')}（{['周一','周二','周三','周四','周五','周六','周日'][today.weekday()]}）。
明天是 {tomorrow.strftime('%Y年%m月%d日')}（{['周一','周二','周三','周四','周五','周六','周日'][tomorrow.weekday()]}）。

=== 任务统计 ===
总任务：{total}
今日已完成：{done_count}
进行中：{len(in_progress)}
待办：{len(todo)}
已过期：{len(overdue)}
明日截止：{len(tomorrow_due)}

=== 今日已完成任务 ===
{chr(10).join(f'- {t["title"]} | {t["category"]} | 预估:{t["hours"]}h' for t in completed_today) if completed_today else '暂无'}

=== 待办任务列表 ===
{chr(10).join(f'- {t["title"]} | 优先级:{t["priority"]} | 截止:{t["deadline"] or "无"} | 预估:{t["hours"]}h | {t["category"]}' for t in todo) if todo else '无'}

=== 进行中任务 ===
{chr(10).join(f'- {t["title"]} | 截止:{t["deadline"] or "无"}' for t in in_progress) if in_progress else '无'}

=== 过期未处理 ===
{chr(10).join(f'- {t["title"]} | 截止:{t["deadline"]} | 预估:{t["hours"]}h | {t["category"]}' for t in overdue) if overdue else '无'}

=== 明日截止 ===
{chr(10).join(f'- {t["title"]} | 优先级:{t["priority"]} | 预估:{t["hours"]}h' for t in tomorrow_due) if tomorrow_due else '明日暂无紧急截止任务'}

请根据以上数据生成晚安播报。"""


def main():
    config = load_env()

    failures = health_check(config)
    if failures:
        print("Health check warnings:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("Health check passed")

    tasks = fetch_active_tasks(config)
    context = build_evening_context(tasks)

    system_prompt = """你是一个温暖贴心的AI代办助手，负责生成晚安播报。
生成格式严格如下（用markdown）：

🌙 晚间代办报告 · 日期（周X）

📊 今日任务小结
- 总任务: X项 | 已完成: X项 | 进行中: X项 | 待办: X项
- 完成率: X%

📋 待办 (X项)
[任务列表，每行: - xxx | 截止X月X日 (状态标签) | Xh | 分类]

💡 智能提示
[1-2条针对性建议]

🗓️ 明日行动建议
[明天重点做什么]

⏰ 时间分配建议
[优先级排序]

💌 温馨提示
[鼓励的话]

✅ 今日已完成 (X项)
[已完成任务列表]

[晚安问候]

语气温暖有安慰感。今天完成得少不要责备，多鼓励。完成得多就表扬。
控制在合理长度。"""

    user_prompt = f"请根据以下数据生成晚安播报：\n\n{context}"

    report = deepseek_chat(config, system_prompt, user_prompt)
    send_message(config, report)
    print("Evening report sent successfully")


if __name__ == "__main__":
    main()
