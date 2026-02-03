import os
from core.common.task import TaskScheduler
from driver.wx.service import login_with_token


def auth():
    login_with_token()


# 以下定时任务由环境变量 WE_RSS.AUTH 控制
# 每小时执行一次，用于刷新授权/会话
# 使用 TaskScheduler 作为长驻后台任务运行
if os.getenv("WE_RSS.AUTH", False):
    auth_task = TaskScheduler()
    auth_task.add_cron_job(auth, "0 */1 * * *", tag="授权定时更新")
    auth_task.start()
