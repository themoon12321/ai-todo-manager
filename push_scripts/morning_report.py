"""AI 代办系统 - 早安播报推送"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_env, health_check, fetch_active_tasks, deepseek_chat, send_message


def build_morning_context(tasks: list) -> str:
    """Build structured morning report data for DeepSeek prompt."""
    today = datetime.date.today()
    week_end = today + datetime.timedelta(days=(6 - today.weekday()))  # 本周日

    today_due = []
    this_week = []
    overdue = []
    no_deadline = []
    completed = []
    in_progress = []
    todo = []

    for t in tasks:
        f = t.get("fields", {})
        status = f.get("状态", "")
        deadline_str = f.get("截止日期", "")

        if status == "已完成":
            completed.append(t)
            continue

        task_info = {
            "title": f.get("标题", ""),
            "priority": f.get("优先级", ""),
            "deadline": deadline_str[:10] if deadline_str else None,
            "hours": f.get("预估时长"),
            "category": f.get("所属分类", ""),
        }

        if status == "进行中":
            in_progress.append(task_info)
        elif status == "待办" or not status:
            todo.append(task_info)

        if task_info["deadline"]:
            try:
                d = datetime.datetime.strptime(task_info["deadline"], "%Y-%m-%d").date()
                if d < today:
                    overdue.append(task_info)
                elif d == today:
                    today_due.append(task_info)
                elif d <= week_end:
                    this_week.append(task_info)
            except ValueError:
                no_deadline.append(task_info)
        else:
            no_deadline.append(task_info)

    return f"""今天是 {today.strftime('%Y年%m月%d日')}（{['周一','周二','周三','周四','周五','周六','周日'][today.weekday()]}）。

=== 任务统计 ===
总任务：{len(tasks)}
已完成：{len(completed)}
进行中：{len(in_progress)}
待办：{len(todo)}
今日截止：{len(today_due)}
本周到期：{len(this_week)}
已过期：{len(overdue)}

=== 今日截止任务 ===
{chr(10).join(f'- {t["title"]} | 优先级:{t["priority"]} | 预估:{t["hours"]}h' for t in today_due) if today_due else '今日暂无截止任务'}

=== 本周紧急任务 ===
{chr(10).join(f'- {t["title"]} | 优先级:{t["priority"]} | 截止:{t["deadline"]} | 预估:{t["hours"]}h' for t in this_week) if this_week else '无'}

=== 过期任务 ===
{chr(10).join(f'- {t["title"]} | 截止:{t["deadline"]} | 预估:{t["hours"]}h' for t in overdue) if overdue else '无'}

=== 进行中任务 ===
{chr(10).join(f'- {t["title"]} | 截止:{t["deadline"] or "无"} | 优先级:{t["priority"]}' for t in in_progress) if in_progress else '无'}

=== 已完成今日 ===
{chr(10).join(f'- {t["title"]}' for t in completed) if completed else '暂无'}

请根据以上数据生成早安播报。"""


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
    context = build_morning_context(tasks)

    system_prompt = """你是一个温暖贴心的AI代办助手，负责生成早安播报。

按以下精确格式生成内容（不要加 markdown 标题或分隔线，全部用纯文本+emoji）：

🌅 早间代办报告 · 日期（周X）

📋 今日待办提醒
[1-2句话概述今日任务情况]

🔥 本周紧急任务（截止本周内）
- 任务: **任务名**, 优先级: **P0/P1等**, 截止日期: **周X或具体日期**, 预估时长: **约Xh**

⚠️ 过期任务提醒（请尽快处理）
- **任务名**, 截止: **日期**, 预估: **约Xh**

💡 早间小贴士
📌 今日重点：[一句话重点]
⏰ 时间分配：[建议]
🌟 温馨提示：[鼓励]

📊 今日任务小结
- 总任务：X
- 已完成：X | 进行中：X | 待办：X
- 完成率：X%

☀️ 早安问候
[简短有力有温度的话]

核心要求：
- 任务名、日期、优先级等关键信息用 **加粗**
- emoji + 文字做分段标题，不用 ### 或 ---
- 每段之间空一行
- 有温度不啰嗦"""

    user_prompt = f"请根据以下数据生成早安播报：\n\n{context}"

    report = deepseek_chat(config, system_prompt, user_prompt)
    send_message(config, report)
    print("Morning report sent successfully")


if __name__ == "__main__":
    main()
