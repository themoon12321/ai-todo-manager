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
    """Call lark-cli and return parsed JSON."""
    cmd = [cli_path] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
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


def send_message(config: dict, message: str):
    """Send message to user's Feishu via lark-cli bot."""
    user_id = config.get("FEISHU_USER_ID", "ou_f5f205e1c2c2527d553b30f191892abc")
    cli = config["LARK_CLI_PATH"]
    try:
        result = subprocess.run(
            [cli, "im", "+messages-send", "--as", "bot",
             "--user-id", user_id, "--markdown", message],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("Message sent via lark-cli (bot)")
        else:
            try:
                err = json.loads(result.stderr)
                msg = err.get("error", {}).get("message", result.stderr)
            except json.JSONDecodeError:
                msg = result.stderr or result.stdout
            print(f"[lark-cli send failed] {msg.strip()}")
            print(f"[message saved to console]\n{message}")
    except Exception as e:
        print(f"[lark-cli error] {e}")
        print(f"[message saved to console]\n{message}")
