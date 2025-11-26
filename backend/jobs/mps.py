import json
from typing import Optional, List, Any

from jobs.article import UpdateArticle, Update_Over
from core.repositories import feed_repo
from core.wx import WxGather
from core.log import logger
from core.task import TaskScheduler
from core.config import cfg
from core.print import print_success, print_error, print_warning
from core.utils import TaskQueue
from core.models import MessageTask
from jobs.webhook import web_hook

# 每隔多少秒执行一次，配置缺失或异常时回退到 60 秒
try:
    INTERVAL: int = int(cfg.get("interval", 60) or 60)
except Exception:
    INTERVAL = 60


def fetch_all_article():
    print("开始更新")
    wx = WxGather().Model()
    try:
        # 获取公众号列表（使用Supabase，同步接口）
        mps = feed_repo.sync_get_feeds()
        for item in mps:
            try:
                # 兼容 dict / 对象两种形式
                faker_id = getattr(item, "faker_id", None) or (
                    item.get("faker_id") if isinstance(item, dict) else None
                )
                mp_id = getattr(item, "id", None) or (
                    item.get("id") if isinstance(item, dict) else None
                )
                mp_name = getattr(item, "mp_name", None) or (
                    item.get("mp_name") if isinstance(item, dict) else None
                )
                wx.get_Articles(
                    faker_id,
                    CallBack=UpdateArticle,
                    Mps_id=mp_id,
                    Mps_title=mp_name,
                    MaxPage=1,
                )
            except Exception as e:
                print_error(e)
        print(wx.articles)
    except Exception as e:
        print_error(e)
    finally:
        logger.info(f"所有公众号更新完成,共更新{wx.all_count()}条数据")


def do_job(mp: Any = None, task: Optional[MessageTask] = None) -> None:
    print("执行任务")
    wx = WxGather().Model()
    try:
        # 兼容 dict / 对象两种形式
        faker_id = getattr(mp, "faker_id", None) or (
            mp.get("faker_id") if isinstance(mp, dict) else None
        )
        mp_id = getattr(mp, "id", None) or (
            mp.get("id") if isinstance(mp, dict) else None
        )
        mp_name = getattr(mp, "mp_name", None) or (
            mp.get("mp_name") if isinstance(mp, dict) else None
        )
        wx.get_Articles(
            faker_id,
            CallBack=UpdateArticle,
            Mps_id=mp_id,
            Mps_title=mp_name,
            MaxPage=1,
            Over_CallBack=Update_Over,
            interval=INTERVAL,
        )
    except Exception as e:
        print_error(e)
    finally:
        count = wx.all_count()
        from jobs.webhook import MessageWebHook

        tms = MessageWebHook(task=task, feed=mp, articles=wx.articles)
        web_hook(tms)
        task_id = getattr(task, "id", "?")
        print_success(f"任务({task_id})[{mp_name}]执行成功,{count}成功条数")

def add_job(
    feeds: Optional[List[Any]] = None,
    task: Optional[MessageTask] = None,
    isTest: bool = False,
) -> None:
    if isTest:
        TaskQueue.clear_queue()
    for feed in feeds or []:
        # 兼容 dict / 对象两种形式，安全获取名称
        mp_name = getattr(feed, "mp_name", None) or (
            feed.get("mp_name") if isinstance(feed, dict) else "未知公众号"
        )

        TaskQueue.add_task(do_job, feed, task)
        if isTest:
            print(f"测试任务，{mp_name}，加入队列成功")
            reload_job()
            break
        print(f"{mp_name}，加入队列成功")
    print_success(TaskQueue.get_queue_info())

def get_feeds(task: Optional[MessageTask] = None) -> Optional[List[Any]]:
    """根据任务配置获取公众号列表。

    优先使用 task.mps_id 中配置的 ID 列表；
    如果解析失败或结果为空，则回退到全部公众号列表。
    """
    if task and getattr(task, "mps_id", None):
        try:
            mps_spec = json.loads(task.mps_id)
            if isinstance(mps_spec, list):
                ids = [item["id"] for item in mps_spec if "id" in item]
                if ids:
                    mps = feed_repo.sync_get_feeds_by_ids(ids)
                    if mps:
                        return mps
        except Exception as e:
            print_error(f"解析任务[{getattr(task, 'id', '?')}]的 mps_id 失败: {e}")

    # 回退到查询全部公众号（同步接口）
    return feed_repo.sync_get_feeds()

scheduler = TaskScheduler()

def reload_job():
    print_success("重载任务")
    scheduler.clear_all_jobs()
    TaskQueue.clear_queue()
    start_job()


def run(job_id: Optional[str] = None, isTest: bool = False):
    from .taskmsg import get_message_task

    tasks = get_message_task(job_id)
    if not tasks:
        print("没有任务")
        return None
    for task in tasks:
        # 添加测试任务
        print_warning(f"{task.name} 添加到队列运行")
        add_job(get_feeds(task), task, isTest=isTest)
        pass
    return tasks


def start_job(job_id: Optional[str] = None) -> None:
    from .taskmsg import get_message_task

    tasks = get_message_task(job_id)
    if not tasks:
        print("没有任务")
        return
    tag = "定时采集"
    for task in tasks:
        cron_exp = task.cron_exp
        if not cron_exp:
            print_error(f"任务[{task.id}]没有设置cron表达式")
            continue

        job_id = scheduler.add_cron_job(
            add_job,
            cron_expr=cron_exp,
            args=[get_feeds(task), task],
            job_id=str(task.id),
            tag="定时采集",
        )
        print(f"已添加任务: {job_id}")
    scheduler.start()
    print("启动任务")


def start_all_task():
    # 开启自动同步未同步 文章任务
    from jobs.fetch_no_article import start_sync_content
    start_sync_content()
    start_job()


if __name__ == "__main__":
    # do_job()
    # start_all_task()
    pass
