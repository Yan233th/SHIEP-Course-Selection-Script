import schedule
import time
import subprocess
import datetime

COMMAND = ["uv", "run", "main.py", "--start"]

def my_task():
    print(f"\n[{datetime.datetime.now()}] 🚀 正在触发预定任务...")
    print(f"执行命令: {' '.join(COMMAND)}")
    subprocess.run(COMMAND)
    return schedule.CancelJob  

# localtime
schedule.every().day.at("13:29:40").do(my_task)
# schedule.every().day.at("12:38:00").do(my_task) # test

print("定时器已启动，等待中...")
while True:
    schedule.run_pending()
    time.sleep(1)