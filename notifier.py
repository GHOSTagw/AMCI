import os
import subprocess
import concurrent.futures
import telegram
from time import sleep

# 从环境变量中获取 Telegram Bot Token 和 Chat ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 初始化 Telegram bot
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# 脚本列表
scripts = [
    'ablesci_GPT_n.py',
    'baidupan_GPT_n.py',
]

# 发送 Telegram 消息的函数
def send_telegram_message(title, message):
    """发送消息到指定的 Telegram chat"""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"标题: {title}\n\n{message}")

# 执行脚本并返回结果
def execute_script(script_name):
    try:
        # 执行脚本并捕获输出
        result = subprocess.run(['python', script_name], capture_output=True, text=True, check=True)
        output = result.stdout
        send_telegram_message(script_name, f"执行成功:\n{output}")
    except subprocess.CalledProcessError as e:
        send_telegram_message(script_name, f"执行失败:\n{e.stderr}")

# 主函数
def main():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 并行执行所有脚本
        executor.map(execute_script, scripts)

if __name__ == "__main__":
    main()
