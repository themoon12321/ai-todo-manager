# AI 代办系统 - 版本日志

## 当前版本: v2.0.0 (2026-06-06)

### 系统架构

```
手机消息 (微信/飞书)
    ↓
CCconnect 中转
    ↓
Claude/DeepSeek Agent（全部业务逻辑：NLP理解 + 分类 + 优先级 + 归档）
    ↓ 调 lark-cli
飞书多维表格（三张表：活跃任务 / 长任务 / 归档）
    ↑
Windows Task Scheduler → Python 脚本 → DeepSeek 润色 → 双渠道推送
```

### 飞书 Base 结构

**Base:** https://kcn3b0pnzw4q.feishu.cn/base/Aq4RbWV1KawnxlsVCCGcvzernoc

**活跃任务表** (tblOH2xP0NcisvbI)
- ID / 标题 / 描述 / 状态 / 优先级(P0🔥~P4⚪) / 所属分类 / 标签(多选) /
- 所属长任务🔗(关联) / 截止日期 / 开始时间 / 完成时间 / 创建时间 /
- 预估时长 / 完成建议 / 来源 / priority_source

**长任务表** (tblWes2ueqV4MtrU)
- 名称 / 状态(未开始/进行中/已结项) / 子任务🔗(关联) / 子任务总数📊 / 已完成子任务数📊

**任务归档表** (tblsMqQeYcAJ67Kv)
- 与活跃任务表同结构（无关联和系统字段）

**视图:** 全部任务(表格) / 看板·状态 / 今日任务 / 日历

### 核心规则

| 规则 | 说明 |
|------|------|
| 优先级 | 5维度打分: 时间40% + 语气20% + 领域20% + 沉寂10% + 依赖10% |
| 优先级调整 | 可自动升级；仅推迟截止时允许降级；用户手动改过的不覆盖 |
| 无DDL任务 | 时间紧迫度计0分，默认P3/P4 |
| 长任务衍生 | 子任务>0→进行中，子任务=0→未开始，仅用户说结项才结项 |
| 归档 | 每次操作顺手检查，completed_at < today 的移入归档表 |
| 手动打勾 | 读取飞书系统"最后更新时间"补完成时间 |

### 推送脚本

- `push_scripts/utils.py` — 公共工具 + 双渠道发送
- `push_scripts/morning_report.py` — 早安播报（DeepSeek 润色）
- `push_scripts/evening_report.py` — 晚安播报（DeepSeek 润色）

**推送格式:**
- 飞书: post 格式 + `<tag>md</tag>` 渲染标题 `###` + 加粗 `**` + hr 分隔
- 微信: 纯文本（去 markdown 符号）

**配置 (.env):**
```
PUSH_CHANNEL=feishu,wechat  # 双渠道；也可单渠道
```

### 定时任务配置命令

```bash
schtasks /create /tn "AI代办-早报" /tr "C:\SoftWare\python\python.exe -X utf8 D:\D_Project\GitHub_Project\AI代办\push_scripts\morning_report.py" /sc daily /st 08:00 /f
schtasks /create /tn "AI代办-晚报" /tr "C:\SoftWare\python\python.exe -X utf8 D:\D_Project\GitHub_Project\AI代办\push_scripts\evening_report.py" /sc daily /st 20:00 /f
```

**注意:** Task Scheduler 需用完整路径执行。

### 文件结构

```
AI代办/
├── SKILL.md                   # AI 技能（完整业务规则）
├── .env                       # 敏感配置（不提交）
├── .env.example               # 配置模板
├── .gitignore
├── setup_base.py              # 一键创建飞书三表
├── push_scripts/
│   ├── utils.py               # 公共工具 + 双渠道推送
│   ├── morning_report.py      # 早安播报
│   └── evening_report.py      # 晚安播报
└── SKILL.md.old               # v1旧版备份
```

### 构建历史

| 日期 | 变更 |
|------|------|
| 2026-06-05 | 项目初始化，设计讨论完成 |
| 2026-06-05 | 重建 SKILL.md，创建飞书三表 |
| 2026-06-05 | 编写 setup_base.py 自动化脚本 |
| 2026-06-06 | 编写早晚报推送脚本 |
| 2026-06-06 | 修复推送格式：改用 post+md 渲染 |
| 2026-06-06 | 添加双渠道：飞书 bot + 微信 cc-connect |
| 2026-06-06 | 解决 Task Scheduler 兼容性问题 |

### 待办 / 已知问题

- WeChat cc-connect 会话 token 可能过期需刷新
- 旧 Base 数据未迁移到新 Base
- 下载的 lark-cli 版本 1.0.39，最新 1.0.48 可更新
