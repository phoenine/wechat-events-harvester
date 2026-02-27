import json
from typing import Optional, List, Any

from jobs.article import UpdateArticle, Update_Over
from core.feeds import feed_repo
from core.feeds.collector import collect_feed_articles
from core.common.log import logger
from core.common.task import TaskScheduler
from core.common.runtime_settings import runtime_settings
from core.common.utils import TaskQueue
from core.message_tasks.model import MessageTask
from jobs.webhook import web_hook

def fetch_all_article():
    logger.info("开始更新")
    total_count = 0
    all_articles = []
    try:
        # 获取公众号列表（使用Supabase，同步接口）
        mps = feed_repo.sync_get_feeds()
        for item in mps:
            try:
                result = collect_feed_articles(
                    item,
                    on_article=UpdateArticle,
                    max_page=1,
                )
                total_count += int(result.get("count", 0))
                all_articles.extend(result.get("articles") or [])
            except Exception as e:
                logger.error(e)
        logger.info(all_articles)
    except Exception as e:
        logger.error(e)
    finally:
        logger.info(f"所有公众号更新完成,共更新{total_count}条数据")


def do_job(mp: Any = None, task: Optional[MessageTask] = None) -> None:
    logger.info("执行任务")
    articles = []
    count = 0
    mp_name = getattr(mp, "mp_name", None) or (
        mp.get("mp_name") if isinstance(mp, dict) else None
    )
    try:
        interval = runtime_settings.get_int_sync("interval", 60)
        result = collect_feed_articles(
            mp,
            on_article=UpdateArticle,
            on_finish=Update_Over,
            max_page=1,
            interval=interval,
        )
        articles = result.get("articles") or []
        count = int(result.get("count", 0))
    except Exception as e:
        logger.error(e)
    finally:
        from jobs.webhook import MessageWebHook

        tms = MessageWebHook(task=task, feed=mp, articles=articles)
        web_hook(tms)
        task_id = getattr(task, "id", "?")
        logger.success(f"任务({task_id})[{mp_name}]执行成功,{count}成功条数")

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
            logger.info(f"测试任务，{mp_name}，加入队列成功")
            reload_job()
            break
        logger.info(f"{mp_name}，加入队列成功")
    logger.success(TaskQueue.get_queue_info())

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
            logger.error(f"解析任务[{getattr(task, 'id', '?')}]的 mps_id 失败: {e}")

    # 回退到查询全部公众号（同步接口）
    return feed_repo.sync_get_feeds()

scheduler = TaskScheduler()

def reload_job():
    logger.success("重载任务")
    scheduler.clear_all_jobs()
    TaskQueue.clear_queue()
    start_job()


def run(job_id: Optional[str] = None, isTest: bool = False):
    from .taskmsg import get_message_task

    tasks = get_message_task(job_id)
    if not tasks:
        logger.info("没有任务")
        return None
    for task in tasks:
        # 添加测试任务
        logger.warning(f"{task.name} 添加到队列运行")
        add_job(get_feeds(task), task, isTest=isTest)
        pass
    return tasks


def start_job(job_id: Optional[str] = None) -> None:
    from .taskmsg import get_message_task

    tasks = get_message_task(job_id)
    if not tasks:
        logger.info("没有任务")
        return
    tag = "定时采集"
    for task in tasks:
        cron_exp = task.cron_exp
        if not cron_exp:
            logger.error(f"任务[{task.id}]没有设置cron表达式")
            continue

        job_id = scheduler.add_cron_job(
            add_job,
            cron_expr=cron_exp,
            args=[get_feeds(task), task],
            job_id=str(task.id),
            tag="定时采集",
        )
        logger.info(f"已添加任务: {job_id}")
    scheduler.start()
    logger.info("启动任务")


def start_all_task():
    # 开启自动同步未同步 文章任务
    from jobs.fetch_no_article import start_sync_content
    start_sync_content()
    start_job()


if __name__ == "__main__":
    # do_job()
    # start_all_task()
    pass
