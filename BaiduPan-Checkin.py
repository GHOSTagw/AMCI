import requests
import time
import re
import os

# 从环境变量中获取 Cookie
# COOKIES = os.environ.get('BAIDU_COOKIE_S')

# F12从 Cookie 获取下面两个值
COOKIES = "BDUSS=xxxx; BAIDUID=xxxx;"

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://pan.baidu.com/wap/svip/growth/task',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cookie': COOKIES
}

def signin():
    url = 'https://pan.baidu.com/rest/2.0/membership/level?app_id=250528&web=5&method=signin'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        sign_point = re.search(r'points":(\d+)', response.text)
        signin_error_msg = re.search(r'"error_msg":"(.*?)"', response.text)
        print(f"签到成功, 获得积分: {sign_point.group(1) if sign_point else '未知'}")
        if signin_error_msg:
            print(f"签到错误信息: {signin_error_msg.group(1)}")
    else:
        print("签到失败")

def delay(seconds):
    time.sleep(seconds)

def get_daily_question():
    url = 'https://pan.baidu.com/act/v2/membergrowv2/getdailyquestion?app_id=250528&web=5'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        answer = re.search(r'"answer":(\d+)', response.text)
        ask_id = re.search(r'"ask_id":(\d+)', response.text)
        if answer and ask_id:
            return answer.group(1), ask_id.group(1)
    return None, None

def answer_question(answer, ask_id):
    url = f'https://pan.baidu.com/act/v2/membergrowv2/answerquestion?app_id=250528&web=5&ask_id={ask_id}&answer={answer}'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        answer_msg = re.search(r'"show_msg":"(.*?)"', response.text)
        answer_score = re.search(r'"score":(\d+)', response.text)
        print(f"答题成功, 获得积分: {answer_score.group(1) if answer_score else '未知'}")
        if answer_msg:
            print(f"答题信息: {answer_msg.group(1)}")
    else:
        print("答题失败")

def get_user_info():
    url = 'https://pan.baidu.com/rest/2.0/membership/user?app_id=250528&web=5&method=query'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        current_value = re.search(r'current_value":(\d+)', response.text)
        current_level = re.search(r'current_level":(\d+)', response.text)
        print(f"当前会员等级: {current_level.group(1) if current_level else '未知'}, 成长值: {current_value.group(1) if current_value else '未知'}")
    else:
        print("获取用户信息失败")

def main():
    signin()
    delay(3)
    answer, ask_id = get_daily_question()
    if answer and ask_id:
        answer_question(answer, ask_id)
    get_user_info()

if __name__ == "__main__":
    main()

# 云函数入口
def handler(event, context):
    main()
