#!/usr/bin/env python
# coding=utf-8

import os
import time
import requests
from bs4 import BeautifulSoup

# ================== Telegram 配置 ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 未配置")
        return

    if len(message) > 4000:
        message = message[:4000] + "\n...(日志过长已截断)"

    title = "科研通\n\n"  # 添加标题
    full_message = title + message  # 在消息前加上标题

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": full_message
            },
            timeout=20
        )
    except Exception as e:
        print("Telegram 发送失败:", e)


# ================== 工具函数 ==================

def protect_privacy(text):
    if not text:
        return text
    if "@" in text:
        parts = text.split("@")
        return parts[0][:2] + "***@" + parts[1]
    return text[:2] + "***"


# ================== 核心类 ==================

class AbleSciAuto:
    def __init__(self, email, password):
        self.session = requests.Session()
        self.email = email
        self.password = password
        self.logs = []

    def get_csrf_token(self):
        try:
            r = self.session.get("https://www.ablesci.com/site/login", timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            token = soup.find('input', {'name': '_csrf'})
            return token.get('value', '') if token else ''
        except Exception as e:
            self.logs.append(f"❌ 获取CSRF异常: {str(e)}")
            return ''

    def login(self):
        token = self.get_csrf_token()
        if not token:
            self.logs.append("❌ 获取CSRF失败")
            return False

        data = {
            "_csrf": token,
            "email": self.email,
            "password": self.password,
            "remember": "off"
        }

        try:
            r = self.session.post(
                "https://www.ablesci.com/site/login",
                data=data,
                timeout=30
            )
        except Exception as e:
            self.logs.append(f"❌ 登录请求异常: {str(e)}")
            return False

        if r.status_code != 200:
            self.logs.append(f"❌ 登录HTTP异常: {r.status_code}")
            self.logs.append(r.text[:500])
            return False

        try:
            result = r.json()
            if result.get("code") == 0:
                return True
            else:
                self.logs.append(f"❌ 登录失败: {result}")
                return False
        except Exception:
            if "退出" in r.text:
                return True

        self.logs.append("❌ 登录未知失败")
        self.logs.append(r.text[:500])
        return False

    def sign_in(self):
        try:
            r = self.session.get("https://www.ablesci.com/user/sign", timeout=30)
        except Exception as e:
            self.logs.append(f"❌ 签到请求异常: {str(e)}")
            return False

        if r.status_code != 200:
            self.logs.append(f"❌ 签到HTTP异常: {r.status_code}")
            self.logs.append(r.text[:500])
            return False

        try:
            result = r.json()
            if result.get("code") == 0:
                return True
            else:
                msg = result.get("msg", "")
                if "已签到" in msg:
                    return True
                self.logs.append(f"❌ 签到失败: {msg}")
                self.logs.append(f"原始返回: {result}")
                return False
        except Exception:
            self.logs.append("❌ 签到JSON解析失败")
            self.logs.append(r.text[:500])
            return False

    def get_user_info(self):
        try:
            r = self.session.get("https://www.ablesci.com/", timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')

            points = soup.select_one('#user-point-now')
            sign_days = soup.select_one('#sign-count')

            points_text = points.text.strip() if points else "未知"
            days_text = sign_days.text.strip() if sign_days else "未知"

            return points_text, days_text

        except Exception as e:
            self.logs.append(f"❌ 获取用户信息异常: {str(e)}")
            return "未知", "未知"

    def run(self):
        self.logs.append(f"账号: {protect_privacy(self.email)}")

        if not self.login():
            return "\n".join(self.logs)

        self.sign_in()
        time.sleep(1)

        points, days = self.get_user_info()

        self.logs.append(f"当前积分: {points}")
        self.logs.append(f"连续签到: {days}天")

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
    accounts = get_accounts()
    if not accounts:
        print("未配置 ABLESCI_ACCOUNTS")
        return

    results = []

    for email, password in accounts:
        bot = AbleSciAuto(email, password)
        results.append(bot.run())

    full_log = "\n\n".join(results)
    send_telegram(full_log)


if __name__ == "__main__":
    main()
