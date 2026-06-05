#!/usr/bin/env python3
"""AI 代办系统 - 飞书多维表格一键创建脚本

用法：
  1. 确保 lark-cli 已安装并登录
  2. python setup_base.py
  3. 将输出的 Base Token 和 Table ID 填入 .env
"""

import subprocess
import json
import sys

LARK_CLI = r"D:\D_software\LarkCLI\lark-cli.cmd"
BASE_NAME = "AI代办"


def run(cmd, desc=""):
    """Run a lark-cli command and return parsed JSON."""
    print(f"\n>>> {desc}..." if desc else f">>> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        try:
            err = json.loads(result.stderr)
            msg = err.get("error", {}).get("message", result.stderr)
        except json.JSONDecodeError:
            msg = result.stderr or result.stdout
        # Some commands return errors but succeeded partially
        print(f"  ⚠ {msg.strip()}")
        return json.loads(result.stdout) if result.stdout else None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  {result.stdout.strip()}")
        return None


def base_create():
    """Step 1: Create a new Base."""
    r = run([
        LARK_CLI, "base", "+base-create",
        "--name", BASE_NAME,
        "--time-zone", "Asia/Shanghai"
    ], "Creating Base")
    if r and r.get("ok"):
        base_token = r["data"]["base"]["base_token"]
        print(f"  ✅ Base created: {base_token}")
        print(f"  📎 {r['data']['base']['url']}")
        return base_token
    return None


def table_create_active(base_token):
    """Step 2: Create the active tasks table."""
    fields = json.dumps([
        {"name": "ID", "type": "text"},
        {"name": "标题", "type": "text"},
        {"name": "描述", "type": "text"},
        {"name": "状态", "type": "select", "options": [
            {"name": "待办"}, {"name": "进行中"},
            {"name": "已完成"}, {"name": "已取消"}
        ]},
        {"name": "优先级", "type": "select", "options": [
            {"name": "P0 🔥", "hue": "Carmine", "lightness": "Lighter"},
            {"name": "P1 🔴", "hue": "Red", "lightness": "Lighter"},
            {"name": "P2 🟡", "hue": "Yellow", "lightness": "Lighter"},
            {"name": "P3 🟢", "hue": "Turquoise", "lightness": "Lighter"},
            {"name": "P4 ⚪", "hue": "Gray", "lightness": "Lighter"}
        ]},
        {"name": "所属分类", "type": "select", "options": [
            {"name": "学业"}, {"name": "生活"},
            {"name": "班务"}, {"name": "项目"}, {"name": "其他"}
        ]},
        {"name": "标签", "type": "select", "multiple": True, "options": [
            {"name": "报告", "hue": "Green"}, {"name": "PPT", "hue": "Orange"},
            {"name": "代码", "hue": "Blue"}, {"name": "文献", "hue": "Purple"},
            {"name": "会议", "hue": "Yellow"}, {"name": "设计", "hue": "Carmine"},
            {"name": "实验报告", "hue": "Red"}, {"name": "考试", "hue": "Yellow"},
            {"name": "作业", "hue": "Carmine"}, {"name": "数据处理", "hue": "Turquoise"},
            {"name": "视频", "hue": "Yellow"}, {"name": "其他", "hue": "Gray"}
        ]},
        {"name": "截止日期", "type": "datetime", "style": {"format": "yyyy/MM/dd"}},
        {"name": "开始时间", "type": "datetime", "style": {"format": "yyyy/MM/dd HH:mm"}},
        {"name": "完成时间", "type": "datetime", "style": {"format": "yyyy/MM/dd"}},
        {"name": "预估时长", "type": "number"},
        {"name": "完成建议", "type": "text"},
        {"name": "来源", "type": "text"},
        {"name": "priority_source", "type": "text"},
        {"name": "创建时间", "type": "created_at", "style": {"format": "yyyy/MM/dd"}},
    ])
    r = run([
        LARK_CLI, "base", "+table-create",
        "--base-token", base_token,
        "--name", "活跃任务表",
        "--fields", fields
    ], "Creating active tasks table")
    if r and r.get("ok"):
        table_id = r["data"]["table"]["id"]
        print(f"  ✅ Active tasks table: {table_id}")
        return table_id
    return None


def table_create_longterm(base_token):
    """Step 3: Create the long-term tasks table."""
    fields = json.dumps([
        {"name": "名称", "type": "text"},
        {"name": "状态", "type": "select", "options": [
            {"name": "未开始"}, {"name": "进行中"}, {"name": "已结项"}
        ]},
    ])
    r = run([
        LARK_CLI, "base", "+table-create",
        "--base-token", base_token,
        "--name", "长任务表",
        "--fields", fields
    ], "Creating long-term tasks table")
    if r and r.get("ok"):
        table_id = r["data"]["table"]["id"]
        print(f"  ✅ Long-term tasks table: {table_id}")
        return table_id
    return None


def table_create_archive(base_token):
    """Step 4: Create the archive table."""
    fields = json.dumps([
        {"name": "ID", "type": "text"},
        {"name": "标题", "type": "text"},
        {"name": "描述", "type": "text"},
        {"name": "状态", "type": "select", "options": [
            {"name": "待办"}, {"name": "进行中"},
            {"name": "已完成"}, {"name": "已取消"}
        ]},
        {"name": "优先级", "type": "select", "options": [
            {"name": "P0 🔥", "hue": "Carmine", "lightness": "Lighter"},
            {"name": "P1 🔴", "hue": "Red", "lightness": "Lighter"},
            {"name": "P2 🟡", "hue": "Yellow", "lightness": "Lighter"},
            {"name": "P3 🟢", "hue": "Turquoise", "lightness": "Lighter"},
            {"name": "P4 ⚪", "hue": "Gray", "lightness": "Lighter"}
        ]},
        {"name": "所属分类", "type": "select", "options": [
            {"name": "学业"}, {"name": "生活"},
            {"name": "班务"}, {"name": "项目"}, {"name": "其他"}
        ]},
        {"name": "标签", "type": "select", "multiple": True, "options": [
            {"name": "报告", "hue": "Green"}, {"name": "PPT", "hue": "Orange"},
            {"name": "代码", "hue": "Blue"}, {"name": "文献", "hue": "Purple"},
            {"name": "会议", "hue": "Yellow"}, {"name": "设计", "hue": "Carmine"},
            {"name": "实验报告", "hue": "Red"}, {"name": "考试", "hue": "Yellow"},
            {"name": "作业", "hue": "Carmine"}, {"name": "数据处理", "hue": "Turquoise"},
            {"name": "视频", "hue": "Yellow"}, {"name": "其他", "hue": "Gray"}
        ]},
        {"name": "截止日期", "type": "datetime", "style": {"format": "yyyy/MM/dd"}},
        {"name": "开始时间", "type": "datetime", "style": {"format": "yyyy/MM/dd HH:mm"}},
        {"name": "完成时间", "type": "datetime", "style": {"format": "yyyy/MM/dd"}},
        {"name": "预估时长", "type": "number"},
        {"name": "完成建议", "type": "text"},
        {"name": "来源", "type": "text"},
    ])
    r = run([
        LARK_CLI, "base", "+table-create",
        "--base-token", base_token,
        "--name", "任务归档表",
        "--fields", fields
    ], "Creating archive table")
    if r and r.get("ok"):
        table_id = r["data"]["table"]["id"]
        print(f"  ✅ Archive table: {table_id}")
        return table_id
    return None


def create_link_fields(base_token, active_table, longterm_table):
    """Step 5: Create linked record fields between tables."""
    # Add "所属长任务" link on active tasks table → long-term table
    run([
        LARK_CLI, "base", "+field-create",
        "--base-token", base_token,
        "--table-id", active_table,
        "--json", json.dumps({
            "name": "所属长任务", "type": "link",
            "link_table": longterm_table
        })
    ], "Creating '所属长任务' link field")

    # Add "子任务" reverse link on long-term table → active tasks table
    run([
        LARK_CLI, "base", "+field-create",
        "--base-token", base_token,
        "--table-id", longterm_table,
        "--json", json.dumps({
            "name": "子任务", "type": "link",
            "link_table": active_table
        })
    ], "Creating '子任务' reverse link field")


def create_lookup_fields(base_token, longterm_table):
    """Step 6: Create lookup fields on long-term table."""
    # Get field IDs for the lookup
    r = run([
        LARK_CLI, "base", "+field-list",
        "--base-token", base_token,
        "--table-id", longterm_table
    ], "Getting long-term table field IDs")
    if not r:
        return

    fields = {f["name"]: f["id"] for f in r["data"]["fields"]}
    name_field_id = fields.get("名称", "名称")

    # Get active table fields
    r2 = run([
        LARK_CLI, "base", "+table-get",
        "--base-token", base_token,
        "--table-id", longterm_table
    ], "Getting table structure")

    # 子任务总数
    run([
        LARK_CLI, "base", "+field-create",
        "--base-token", base_token,
        "--table-id", longterm_table,
        "--i-have-read-guide",
        "--json", json.dumps({
            "type": "lookup", "name": "子任务总数",
            "from": "活跃任务表", "select": "ID",
            "aggregate": "counta",
            "where": {
                "logic": "and",
                "conditions": [
                    ["所属长任务", "intersects", {"type": "field_ref", "field": "名称"}]
                ]
            }
        })
    ], "Creating '子任务总数' lookup field")

    # 已完成子任务数
    run([
        LARK_CLI, "base", "+field-create",
        "--base-token", base_token,
        "--table-id", longterm_table,
        "--i-have-read-guide",
        "--json", json.dumps({
            "type": "lookup", "name": "已完成子任务数",
            "from": "活跃任务表", "select": "ID",
            "aggregate": "counta",
            "where": {
                "logic": "and",
                "conditions": [
                    ["所属长任务", "intersects", {"type": "field_ref", "field": "名称"}],
                    ["状态", "==", {"type": "constant", "value": ["已完成"]}]
                ]
            }
        })
    ], "Creating '已完成子任务数' lookup field")


def cleanup_default_table(base_token):
    """Step 7: Delete the default empty table created with the Base."""
    r = run([
        LARK_CLI, "base", "+table-list",
        "--base-token", base_token
    ], "Listing tables to find default table")
    if not r:
        return
    for t in r["data"]["tables"]:
        if t["name"] == "数据表":
            run([
                LARK_CLI, "base", "+table-delete",
                "--base-token", base_token,
                "--table-id", t["id"],
                "--yes"
            ], f"Deleting default table '{t['name']}'")


def main():
    print("=" * 50)
    print("  AI 代办系统 - 飞书 Base 自动化创建")
    print("=" * 50)

    # Step 1: Create Base
    base_token = base_create()
    if not base_token:
        print("❌ Failed to create Base")
        sys.exit(1)

    # Step 2: Create active tasks table
    active_table = table_create_active(base_token)
    if not active_table:
        print("❌ Failed to create active tasks table")
        sys.exit(1)

    # Step 3: Create long-term tasks table
    longterm_table = table_create_longterm(base_token)
    if not longterm_table:
        print("❌ Failed to create long-term tasks table")
        sys.exit(1)

    # Step 4: Create archive table
    archive_table = table_create_archive(base_token)
    if not archive_table:
        print("❌ Failed to create archive table")
        sys.exit(1)

    # Step 5: Create link fields
    create_link_fields(base_token, active_table, longterm_table)

    # Step 6: Create lookup fields
    create_lookup_fields(base_token, longterm_table)

    # Step 7: Cleanup default table
    cleanup_default_table(base_token)

    # Output results
    print("\n" + "=" * 50)
    print("  ✅ 创建完成！请将以下信息填入 .env")
    print("=" * 50)
    print(f"\nFEISHU_BASE_TOKEN={base_token}")
    print(f"FEISHU_ACTIVE_TABLE={active_table}")
    print(f"FEISHU_LONGTERM_TABLE={longterm_table}")
    print(f"FEISHU_ARCHIVE_TABLE={archive_table}")
    print(f"\n📎 Base 链接:")
    print(f"https://kcn3b0pnzw4q.feishu.cn/base/{base_token}")


if __name__ == "__main__":
    main()
