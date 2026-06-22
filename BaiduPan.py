import os
import time
import requests

# ================= 配置初始化 =================
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

# [优化点 1] 提取公共请求参数，避免每次手动拼接 URL
session.params = {
    "app_id": "250528",
    "web": "5"
}

if BAIDU_COOKIE.strip():
    session.headers.update({"Cookie": BAIDU_COOKIE})

# =================================================

def add_message(msg: str):
    print(msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")) # 终端打印纯文本
    final_messages.append(msg)

def signin():
    if not BAIDU_COOKIE.strip():
        add_message("❌ <b>自动签到：</b>未检测到有效的 BAIDU_COOKIE")
        return
    
    url = "https://pan.baidu.com/rest/2.0/membership/level?method=signin"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            # [优化点 2] 使用 JSON 状态码 errno 替代脆弱的正则表达式
            errno = res_data.get("errno", -1)
            if errno == 0:
                points = res_data.get("points", "未知")
                add_message(f"✅ <b>自动签到：</b>成功 (获得积分: <code>{points}</code>)")
            else:
                error_msg = res_data.get("error_msg") or res_data.get("errmsg") or "原因未知，可能是Cookie失效"
                add_message(f"❌ <b>自动签到：</b>失败 (错误码: {errno}, 原因: {error_msg})")
        else:
            add_message(f"❌ <b>自动签到：</b>HTTP 请求异常 (状态码: {resp.status_code})")
    except Exception as e:
        add_message(f"⚠️ <b>自动签到：</b>网络或系统异常 ({e})")

def get_daily_question():
    if not BAIDU_COOKIE.strip():
        return None, None
    
    url = "https://pan.baidu.com/act/v2/membergrowv2/getdailyquestion"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            if res_data.get("errno") == 0:
                answer = res_data.get("answer")
                ask_id = res_data.get("ask_id")
                if answer is not None and ask_id is not None:
                    return answer, ask_id
                add_message("⚠️ <b>每日答题：</b>成功获取题目，但未找到答案或问题ID数据")
            else:
                error_msg = res_data.get("error_msg") or "无法获取题目"
                add_message(f"⚠️ <b>每日答题：</b>获取题目失败 ({error_msg})")
        else:
            add_message(f"❌ <b>每日答题：</b>获取题目 HTTP 异常 ({resp.status_code})")
    except Exception as e:
        add_message(f"⚠️ <b>每日答题：</b>获取题目系统异常 ({e})")
    return None, None

def answer_question(answer, ask_id):
    url = "https://pan.baidu.com/act/v2/membergrowv2/answerquestion"
    # 将临时参数追加进请求中
    params = {"ask_id": ask_id, "answer": answer}
    try:
        resp = session.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            if res_data.get("errno") == 0 or "score" in res_data:
                score = res_data.get("score", "0")
                msg = res_data.get("show_msg", "回答正确")
                add_message(f"🎯 <b>每日答题：</b>成功 (获得成长值: <code>{score}</code>, 结果: {msg})")
            else:
                add_message(f"❌ <b>每日答题：</b>提交答案失败 (返回: {res_data})")
        else:
            add_message(f"❌ <b>每日答题：</b>提交答案 HTTP 异常 ({resp.status_code})")
    except Exception as e:
        add_message(f"⚠️ <b>每日答题：</b>答题系统异常 ({e})")

def get_user_info():
    url = "https://pan.baidu.com/rest/2.0/membership/user?method=query"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            current_level = res_data.get("current_level", "未知")
            current_value = res_data.get("current_value", "未知")
            add_message(f"📊 <b>账户信息：</b>当前等级 <code>LV{current_level}</code> | 成长值 <code>{current_value}</code>")
        else:
            add_message(f"❌ <b>用户信息：</b>获取失败 (状态码: {resp.status_code})")
    except Exception as e:
        add_message(f"⚠️ <b>用户信息：</b>系统异常 ({e})")

def send_telegram_once(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 参数缺失，跳过发送")
        return
    
    # [优化点 4] 使用 Telegram HTML 样式模板包装，使其更加美观
    telegram_html = (
        "<b>🤖 百度网盘自动化助手报告</b>\n"
        "<code>──────────────────────</code>\n"
        f"{message}\n"
        "<code>──────────────────────</code>\n"
        f"⏰ <i>执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": telegram_html,
        "parse_mode": "HTML"  # 指定使用 HTML 格式解析消息
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"Telegram 发送失败: {resp.text}")
    except Exception as e:
        print("Telegram异常:", e)

def main():
    signin()
    time.sleep(3)
    answer, ask_id = get_daily_question()
    if answer is not None and ask_id is not None:
        answer_question(answer, ask_id)
    get_user_info()
    
    if final_messages:
        send_telegram_once("\n".join(final_messages))

if __name__ == "__main__":
    main()
