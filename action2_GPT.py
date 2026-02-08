import os
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BAIDU_COOKIE = os.getenv("BAIDU_COOKIE")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://pan.baidu.com/",
}

def human_sleep(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


def create_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    session.headers.update(HEADERS)

    if BAIDU_COOKIE:
        session.headers["Cookie"] = BAIDU_COOKIE

    return session


def telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Telegram 未配置，跳过通知")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": TG_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Telegram 发送失败:", e)


def signin(session):
    url = "https://pan.baidu.com/rest/2.0/membership/user/signin"

    r = session.get(url, timeout=15)
    data = r.json()

    if data.get("errno") != 0:
        raise Exception(f"签到失败: {data}")

    points = data.get("points", 0)
    return points


def get_daily_question(session):
    url = "https://pan.baidu.com/rest/2.0/membership/user/getquestion"

    r = session.get(url, timeout=15)
    data = r.json()

    if data.get("errno") != 0:
        raise Exception("获取问题失败")

    return data["question"]["id"], data["question"]["answer"]


def answer_question(session, qid, answer):
    url = "https://pan.baidu.com/rest/2.0/membership/user/answerquestion"

    params = {
        "qid": qid,
        "answer": answer
    }

    r = session.get(url, params=params, timeout=15)
    data = r.json()

    if data.get("errno") != 0:
        raise Exception("答题失败")

    return data.get("points", 0)


def get_user_info(session):
    url = "https://pan.baidu.com/rest/2.0/membership/user/info"

    r = session.get(url, timeout=15)
    data = r.json()

    if data.get("errno") != 0:
        raise Exception("获取用户信息失败")

    return data["user_info"]["username"], data["user_info"]["total_points"]


def main():
    if not BAIDU_COOKIE:
        raise RuntimeError("未设置 BAIDU_COOKIE")

    session = create_session()

    try:
        sign_points = signin(session)
        human_sleep()

        qid, answer = get_daily_question(session)
        human_sleep()

        quiz_points = answer_question(session, qid, answer)
        human_sleep()

        username, total = get_user_info(session)

        msg = (
            f"✅ 百度网盘签到成功\n\n"
            f"👤 用户：{username}\n"
            f"🎁 签到积分：{sign_points}\n"
            f"🧠 答题积分：{quiz_points}\n"
            f"💰 当前总积分：{total}"
        )

        print(msg)
        telegram(msg)

    except Exception as e:
        err = f"❌ 百度签到异常\n\n{e}"
        print(err)
        telegram(err)


if __name__ == "__main__":
    main()
