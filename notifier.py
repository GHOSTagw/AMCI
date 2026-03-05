#!/usr/bin/env python
# coding=utf-8

import os
import subprocess
import datetime
import requests

# ================== Telegram 配置 ==================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 是否仅在失败时发送
ONLY_FAIL_NOTIFY = os.getenv("ONLY_FAIL_NOTIFY", "false").lower() == "true"

# 需要执行的脚本列表
SCRIPTS = [
    "ablesci_GPT_n.py",
    # 以后新增脚本只需在这里加
]


# ================== Telegram 发送 ==================

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 未配置")
        return

    # Telegram 单条限制 4096
    if len(message) > 4000:
        message = message[:4000] + "\n\n...(日志过长已截断)"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=30
        )
    except Exception as e:
        print("Telegram 发送异常:", e)


# ================== 执行脚本 ==================

def run_script(script_name):
    try:
        result = subprocess.run(
            ["python3", script_name],
            capture_output=True,
            text=True,
            timeout=300
        )

        output = result.stdout.strip()
        error = result.stderr.strip()
        exit_code = result.returncode

        return {
            "name": script_name,
            "exit_code": exit_code,
            "stdout": output,
            "stderr": error
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
            "stderr": f"执行异常: {str(e)}"
        }


# ================== 主逻辑 ==================

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []
    has_fail = False

    for script in SCRIPTS:
        result = run_script(script)
        results.append(result)

        if result["exit_code"] != 0:
            has_fail = True

    # 如果设置为仅失败通知
    if ONLY_FAIL_NOTIFY and not has_fail:
        print("全部成功，不发送通知")
        return

    # 组装最终日志
    message_lines = []
    message_lines.append(f"📅 执行时间: {now}")
    message_lines.append("")

    for r in results:
        status = "✅ 成功" if r["exit_code"] == 0 else f"❌ 失败 (code={r['exit_code']})"
        message_lines.append(f"【{r['name']}】{status}")
        message_lines.append("")

        if r["stdout"]:
            message_lines.append(r["stdout"])
            message_lines.append("")

        if r["stderr"]:
            message_lines.append("⚠️ STDERR:")
            message_lines.append(r["stderr"])
            message_lines.append("")

        message_lines.append("=" * 40)

    final_message = "\n".join(message_lines)
    send_telegram(final_message)


if __name__ == "__main__":
    main()
