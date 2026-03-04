#!/usr/bin/env python
# coding=utf-8

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
import json
import datetime

# ================== Telegram 配置 ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 未配置")
        return
    
    if len(message) > 4000:
        message = message[:4000] + "\n...(日志过长已截断)"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=20
        )
        print("Telegram 通知发送成功")
    except Exception as e:
        print("Telegram 发送失败:", e)


# ================== 工具函数 ==================

def protect_privacy(text):
    if not text:
        return text
    if "@" in text:
        parts = text.split("@")
        return parts[0][:2] + "***@" + parts[1]
    return text[:2] + "***" if len(text) > 2 else "***"


def log(msg_list, message, level="info"):
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + datetime.timedelta(hours=8)
    timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    symbol_map = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }

    symbol = symbol_map.get(level, "ℹ️")
    log_msg = f"[{timestamp}] {symbol} {message}"
    print(log_msg)
    msg_list.append(log_msg)


# ================== 核心类 ==================

class AbleSciAuto:
    def __init__(self, email, password):
        self.session = requests.Session()
        self.email = email
        self.password = password
        self.logs = []
        self.start_time = time.time()

        log(self.logs, f"处理账号: {protect_privacy(email)}")

    def get_csrf_token(self):
        url = "https://www.ablesci.com/site/login"
        r = self.session.get(url, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        token = soup.find('input', {'name': '_csrf'})
        return token.get('value', '') if token else ''

    def login(self):
        token = self.get_csrf_token()
        if not token:
            log(self.logs, "获取CSRF失败", "error")
            return False

        data = {
            "_csrf": token,
            "email": self.email,
            "password": self.password,
            "remember": "off"
        }

        r = self.session.post(
            "https://www.ablesci.com/site/login",
            data=data,
            timeout=30
        )

        if r.status_code == 200:
            try:
                result = r.json()
                if result.get("code") == 0:
                    log(self.logs, "登录成功", "success")
                    return True
                else:
                    log(self.logs, f"登录失败: {result.get('msg')}", "error")
            except:
                if "退出" in r.text:
                    log(self.logs, "登录成功", "success")
                    return True

        log(self.logs, "登录失败", "error")
        return False

    def get_user_info(self):
        r = self.session.get("https://www.ablesci.com/", timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')

        username = soup.select_one('.mobile-hide.able-head-user-vip-username')
        points = soup.select_one('#user-point-now')
        sign_days = soup.select_one('#sign-count')

        if username:
            log(self.logs, f"用户名: {protect_privacy(username.text.strip())}")
        if points:
            log(self.logs, f"当前积分: {points.text.strip()}")
        if sign_days:
            log(self.logs, f"连续签到: {sign_days.text.strip()}天")

    def sign_in(self):
        r = self.session.get("https://www.ablesci.com/user/sign", timeout=30)
        if r.status_code == 200:
            try:
                result = r.json()
                if result.get("code") == 0:
                    log(self.logs, f"签到成功: {result.get('msg')}", "success")
                    return True
                else:
                    msg = result.get("msg", "")
                    if "已签到" in msg:
                        log(self.logs, "今日已签到", "info")
                        return True
                    log(self.logs, f"签到失败: {msg}", "error")
            except:
                log(self.logs, "签到响应解析失败", "error")
        return False

    def run(self):
        if self.login():
            self.get_user_info()
            self.sign_in()
            time.sleep(2)
            self.get_user_info()

        elapsed = round(time.time() - self.start_time, 2)
        log(self.logs, f"执行耗时: {elapsed}秒")

        return "\n".join(self.logs)


# ================== 多账号支持 ==================

def get_accounts():
    raw = os.getenv("ABLESCI_ACCOUNTS")
    if not raw:
        return []

    accounts = []
    for line in raw.splitlines():
        if ":" in line:
            email, password = line.split(":", 1)
            accounts.append((email.strip(), password.strip()))
    return accounts


# ================== 主函数 ==================

def main():
    all_logs = []
    accounts = get_accounts()

    if not accounts:
        print("未配置 ABLESCI_ACCOUNTS")
        return

    for i, (email, password) in enumerate(accounts, 1):
        print(f"\n===== 账号 {i}/{len(accounts)} =====")
        bot = AbleSciAuto(email, password)
        log_text = bot.run()
        all_logs.append(log_text)

    full_log = "\n\n".join(all_logs)

    # 发送 Telegram 通知
    send_telegram(full_log)


if __name__ == "__main__":
    main()
