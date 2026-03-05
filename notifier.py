#!/usr/bin/env python
# coding=utf-8

import os
import sys
import subprocess
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================== Telegram 配置 ==================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ONLY_FAIL_NOTIFY = os.getenv("ONLY_FAIL_NOTIFY", "false").lower() == "true"

# 手动维护脚本
SCRIPTS = [
    "ablesci_GPT_n.py",
    "action_baidu_sign.py",
]

# ================== Telegram ==================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 未配置")
        return

    if len(message) > 4000:
        message = message[:4000] + "\n...(日志过长已截断)"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:

        resp = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=30
        )

        if resp.status_code != 200:
            print("Telegram发送失败:", resp.text)

    except Exception as e:
        print("Telegram异常:", e)


# ================== 执行脚本 ==================

def run_script(script_name):

    if not os.path.exists(script_name):
        return {
            "name": script_name,
            "exit_code": 97,
            "stdout": "",
            "stderr": "脚本不存在"
        }

    try:

        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            "name": script_name,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except subprocess.TimeoutExpired:

        return {
            "name": script_name,
            "exit_code": 99,
            "stdout": "",
            "stderr": "脚本执行超时"
        }

    except Exception as e:

        return {
            "name": script_name,
            "exit_code": 98,
            "stdout": "",
            "stderr": str(e)
        }


# ================== 单脚本处理 ==================

def process_script(script):

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    r = run_script(script)

    status = "✅ 成功" if r["exit_code"] == 0 else f"❌ 失败 (code={r['exit_code']})"

    if ONLY_FAIL_NOTIFY and r["exit_code"] == 0:
        return

    message_lines = []

    message_lines.append(f"📅 执行时间: {now}")
    message_lines.append(f"脚本: {script}")
    message_lines.append(f"状态: {status}")
    message_lines.append("")

    if r["stdout"]:
        message_lines.append(r["stdout"])
        message_lines.append("")

    if r["stderr"]:
        message_lines.append("⚠️ STDERR:")
        message_lines.append(r["stderr"])
        message_lines.append("")

    message = "\n".join(message_lines)

    send_telegram(message)


# ================== 主函数 ==================

def main():

    with ThreadPoolExecutor(max_workers=len(SCRIPTS)) as executor:

        futures = [executor.submit(process_script, s) for s in SCRIPTS]

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
