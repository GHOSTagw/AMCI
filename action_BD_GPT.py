import time
import re
import os
import requests

BAIDU_COOKIE = os.getenv("BAIDU_COOKIE", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://pan.baidu.com/wap/svip/growth/task',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

final_messages = []

# ================= Session 初始化 =================

session = requests.Session()
session.headers.update(HEADERS)

if BAIDU_COOKIE.strip():
    session.headers.update({"Cookie": BAIDU_COOKIE})

# =================================================


def add_message(msg: str):
    print(msg)
    final_messages.append(msg)


def signin():
    if not BAIDU_COOKIE.strip():
        add_message("未检测到 BAIDU_COOKIE")
        return

    url = "https://pan.baidu.com/rest/2.0/membership/level?app_id=250528&web=5&method=signin"

    try:
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:
            sign_point = re.search(r'points":(\d+)', resp.text)
            signin_error_msg = re.search(r'"error_msg":"(.*?)"', resp.text)

            if sign_point:
                add_message(f"签到成功, 获得积分: {sign_point.group(1)}")
            else:
                add_message("签到成功, 但未检索到积分")

            if signin_error_msg and signin_error_msg.group(1):
                add_message(f"签到错误信息: {signin_error_msg.group(1)}")

        else:
            add_message(f"签到失败: {resp.status_code}")

    except Exception as e:
        add_message(f"签到异常: {e}")


def get_daily_question():
    if not BAIDU_COOKIE.strip():
        return None, None

    url = "https://pan.baidu.com/act/v2/membergrowv2/getdailyquestion?app_id=250528&web=5"

    try:
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:
            answer = re.search(r'"answer":(\d+)', resp.text)
            ask_id = re.search(r'"ask_id":(\d+)', resp.text)

            if answer and ask_id:
                return answer.group(1), ask_id.group(1)
            else:
                add_message("未找到问题数据")

        else:
            add_message(f"获取问题失败: {resp.status_code}")

    except Exception as e:
        add_message(f"获取问题异常: {e}")

    return None, None


def answer_question(answer, ask_id):
    url = (
        "https://pan.baidu.com/act/v2/membergrowv2/answerquestion"
        f"?app_id=250528&web=5&ask_id={ask_id}&answer={answer}"
    )

    try:
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:
            answer_msg = re.search(r'"show_msg":"(.*?)"', resp.text)
            answer_score = re.search(r'"score":(\d+)', resp.text)

            if answer_score:
                add_message(f"答题成功, 获得积分: {answer_score.group(1)}")
            else:
                add_message("答题成功, 未检索到积分")

            if answer_msg and answer_msg.group(1):
                add_message(f"答题信息: {answer_msg.group(1)}")

        else:
            add_message(f"答题失败: {resp.status_code}")

    except Exception as e:
        add_message(f"答题异常: {e}")


def get_user_info():
    url = "https://pan.baidu.com/rest/2.0/membership/user?app_id=250528&web=5&method=query"

    try:
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:
            current_value = re.search(r'current_value":(\d+)', resp.text)
            current_level = re.search(r'current_level":(\d+)', resp.text)

            add_message(
                f"当前会员等级: {current_level.group(1) if current_level else '未知'}, "
                f"成长值: {current_value.group(1) if current_value else '未知'}"
            )

        else:
            add_message(f"获取用户信息失败: {resp.status_code}")

    except Exception as e:
        add_message(f"用户信息异常: {e}")


def send_telegram_once(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 参数缺失")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }, timeout=10)

    except Exception as e:
        print("Telegram异常:", e)


def main():
    signin()
    time.sleep(3)

    answer, ask_id = get_daily_question()
    if answer and ask_id:
        answer_question(answer, ask_id)

    get_user_info()

    if final_messages:
        send_telegram_once("\n".join(final_messages))


if __name__ == "__main__":
    main()
