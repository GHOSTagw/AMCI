import time
import re
import os
import requests

BAIDU_COOKIE = os.getenv("BAIDU_COOKIE", "")

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://pan.baidu.com/wap/svip/growth/task',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

final_messages = []
has_error = False

# ================= Session =================

session = requests.Session()
session.headers.update(HEADERS)

if BAIDU_COOKIE.strip():
    session.headers.update({"Cookie": BAIDU_COOKIE})


# ================= 工具 =================

def add_message(msg: str):
    print(msg)
    final_messages.append(msg)


def add_error(msg: str):
    global has_error
    has_error = True
    add_message("❌ " + msg)


# ================= 功能 =================

def signin():
    if not BAIDU_COOKIE.strip():
        add_error("未检测到 BAIDU_COOKIE")
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
                add_message("签到成功, 未检测到积分")

            if signin_error_msg and signin_error_msg.group(1):
                add_message(f"签到提示: {signin_error_msg.group(1)}")

        else:
            add_error(f"签到失败: {resp.status_code}")

    except Exception as e:
        add_error(f"签到异常: {e}")


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

            add_message("未找到答题数据")

        else:
            add_error(f"获取问题失败: {resp.status_code}")

    except Exception as e:
        add_error(f"获取问题异常: {e}")

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
                add_message("答题成功, 未检测到积分")

            if answer_msg and answer_msg.group(1):
                add_message(f"答题提示: {answer_msg.group(1)}")

        else:
            add_error(f"答题失败: {resp.status_code}")

    except Exception as e:
        add_error(f"答题异常: {e}")


def get_user_info():

    url = "https://pan.baidu.com/rest/2.0/membership/user?app_id=250528&web=5&method=query"

    try:
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:

            current_value = re.search(r'current_value":(\d+)', resp.text)
            current_level = re.search(r'current_level":(\d+)', resp.text)

            add_message(
                f"会员等级: {current_level.group(1) if current_level else '未知'}, "
                f"成长值: {current_value.group(1) if current_value else '未知'}"
            )

        else:
            add_error(f"获取用户信息失败: {resp.status_code}")

    except Exception as e:
        add_error(f"用户信息异常: {e}")


# ================= 主函数 =================

def main():

    signin()
    time.sleep(2)

    answer, ask_id = get_daily_question()

    if answer and ask_id:
        answer_question(answer, ask_id)

    get_user_info()

    print("-" * 40)

    return 1 if has_error else 0


if __name__ == "__main__":
    exit(main())
