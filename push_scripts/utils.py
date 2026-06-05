"""AI 代办系统 - 推送脚本公共工具"""

import os
import json
import subprocess
import requests
from pathlib import Path


def load_env(env_path: str = None) -> dict:
    """Load .env file and return config dict."""
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"

    config = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()
    return config


def call_lark(cli_path: str, *args) -> dict:
    """Call lark-cli and return parsed JSON.
    cli_path: path to lark-cli directory (e.g. D:\\D_software\\LarkCLI)
    """
    node_script = os.path.join(cli_path, "node_modules", "@larksuite", "cli", "scripts", "run.js")
    cmd = ["node", node_script] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cli_path)
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli error: {result.stderr}")
    return json.loads(result.stdout)


def fetch_active_tasks(config: dict) -> list:
    """Fetch all records from the active tasks table."""
    r = call_lark(
        config["LARK_CLI_PATH"],
        "base", "+record-list", "--format", "json",
        "--base-token", config["FEISHU_BASE_TOKEN"],
        "--table-id", config["FEISHU_ACTIVE_TABLE"]
    )
    # JSON format returns data as arrays indexed by fields
    data = r.get("data", {})
    fields = data.get("fields", [])
    rows = data.get("data", [])
    record_ids = data.get("record_id_list", [])

    result = []
    for i, row in enumerate(rows):
        record = {"id": record_ids[i] if i < len(record_ids) else "", "fields": {}}
        for j, val in enumerate(row):
            if j < len(fields):
                field_name = fields[j]
                # Clean up: select fields return lists, extract first value
                if isinstance(val, list):
                    if val and isinstance(val[0], str):
                        val = val[0]
                    elif val and isinstance(val[0], dict) and "name" in val[0]:
                        val = val[0]["name"]
                    elif not val:
                        val = ""
                record["fields"][field_name] = val
        result.append(record)
    return result


def health_check(config: dict) -> list:
    """Check Feishu API and DeepSeek API, return list of failures."""
    failures = []

    # Check lark-cli connectivity
    try:
        r = call_lark(
            config["LARK_CLI_PATH"],
            "base", "+table-list",
            "--base-token", config["FEISHU_BASE_TOKEN"]
        )
        if not r.get("ok"):
            failures.append(f"飞书 API 连接失败: {r.get('error', {}).get('message', 'unknown')}")
    except Exception as e:
        failures.append(f"飞书 API 异常: {e}")

    # Check DeepSeek API availability
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['DEEPSEEK_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.get("DEEPSEEK_MODEL", "deepseek-chat"),
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            },
            timeout=10
        )
        if resp.status_code == 402:
            failures.append("DeepSeek API 余额不足")
        elif resp.status_code != 200:
            failures.append(f"DeepSeek API 异常: HTTP {resp.status_code}")
    except Exception as e:
        failures.append(f"DeepSeek API 连接失败: {e}")

    return failures


def deepseek_chat(config: dict, system_prompt: str, user_prompt: str) -> str:
    """Call DeepSeek API and return the response text."""
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": config.get("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def send_feishu(config: dict, message: str):
    """Send message via lark-cli bot (markdown)."""
    user_id = config.get("FEISHU_USER_ID", "ou_f5f205e1c2c2527d553b30f191892abc")
    lark_dir = config.get("LARK_CLI_PATH", r"D:\D_software\LarkCLI")
    node_script = os.path.join(lark_dir, "node_modules", "@larksuite", "cli", "scripts", "run.js")

    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(message)
    tmp.close()

    try:
        cmd = f'node "{node_script}" im +messages-send --as bot --user-id {user_id} --markdown "$(cat \'{tmp.name}\')"'
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=30, cwd=lark_dir)
        out = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        err = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        if result.returncode == 0:
            print("Message sent via feishu bot"); return True
        print(f"[feishu send failed] {err.strip() or out.strip()}"); return False
    except Exception as e:
        print(f"[feishu error] {e}"); return False
    finally:
        os.unlink(tmp.name)


def send_wechat(config: dict, message: str):
    """Send message via cc-connect to WeChat."""
    data_dir = config.get("CC_DATA_DIR", r"D:\D_software\cc-connect\data")
    project = config.get("CC_PROJECT", "wechat")
    message = message.replace("\\n", "\n").strip().replace("*", "")
    try:
        cmd = f'cc-connect send -m "{message}" -p {project} --data-dir "{data_dir}"'
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=30)
        out = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        err = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        if result.returncode == 0:
            print("Message sent via wechat"); return True
        print(f"[wechat send failed] {err.strip() or out.strip()}"); return False
    except Exception as e:
        print(f"[wechat error] {e}"); return False


def send_message(config: dict, message: str):
    """Send message via configured channel(s)."""
    message = message.replace("\\n", "\n").strip()
    channels = config.get("PUSH_CHANNEL", "feishu").split(",")
    ok = False
    for ch in channels:
        ch = ch.strip()
        if ch == "feishu":
            ok = send_feishu(config, message) or ok
        elif ch == "wechat":
            ok = send_wechat(config, message) or ok
        else:
            print(f"[unknown channel] {ch}")
    if not ok:
        print(f"[message saved to console]\n{message}")
