from core.integrations.wx import create_gather
from time import sleep
import random

from core.common.log import logger
from core.common.runtime_settings import runtime_settings
from driver.wx.service import fetch_article as wx_fetch_article
from core.articles import article_repo
from core.common.status import DataStatus as DATA_STATUS


def fetch_articles_without_content():
    """查询content为空的文章, 调用微信内容提取方法获取内容并更新数据库"""
    ga = create_gather()
    try:
        # 查询content为空的文章
        articles = article_repo.sync_get_articles(
                filters={"or": [{"content": {"is": None}}, {"content": {"eq": ""}}]},
                limit=10,
            )

        if not articles:
            logger.warning("暂无需要获取内容的文章")
            return

        for article in articles:
            # 构建URL
            if article.get("url"):
                url = article.get("url")
            else:
                url = f"https://mp.weixin.qq.com/s/{article.get('id')}"

            logger.info(f"正在处理文章: {article.get('title')}, URL: {url}")

            # 获取内容（同步方式）
            content_mode = runtime_settings.get_sync("gather.content_mode", "web")
            if str(content_mode).strip().lower() == "web":
                env = wx_fetch_article(url)
                if env.get("ok"):
                    content_data = env.get("data") or {}
                    content = (content_data or {}).get("content")
                else:
                    err = env.get("error") or {}
                    logger.error(
                        f"抓取文章失败: code={err.get('code')} reason={err.get('reason') or err.get('message')}"
                    )
                    content = None
            else:
                content = ga.content_extract(url)

            # 随机延迟，避免频繁请求
            sleep(random.randint(3, 10))

            if content:
                # 更新内容
                update_data = {"content": content}
                if content == "DELETED":
                    logger.error(f"获取文章 {article.get('title')} 内容已被发布者删除")
                    update_data["status"] = DATA_STATUS.DELETED

                article_repo.sync_update_article(article.get("id"), update_data)
                logger.success(f"成功更新文章 {article.get('title')} 的内容")
            else:
                logger.error(f"获取文章 {article.get('title')} 内容失败")

    except Exception as e:
        logger.info(f"处理过程中发生错误: {e}")
    finally:
        # wx_service.fetch_article 内部会自行管理抓取器的浏览器生命周期，这里无需额外 Close
        pass


from core.common.task import TaskScheduler
from core.common.utils import TaskQueue

scheduler = TaskScheduler()
task_queue = TaskQueue


def start_sync_content():
    if not runtime_settings.get_bool_sync("gather.content_auto_check", False):
        logger.warning("自动检查并同步文章内容功能未启用")
        return
    interval = runtime_settings.get_int_sync("gather.content_auto_interval", 1)  # 每隔多少分钟
    cron_exp = f"*/{interval} * * * *"
    task_queue.clear_queue()
    scheduler.clear_all_jobs()

    def do_sync():
        task_queue.add_task(fetch_articles_without_content)

    job_id = scheduler.add_cron_job(do_sync, cron_expr=cron_exp)
    logger.success(f"已添自动同步文章内容任务: {job_id}")
    scheduler.start()


if __name__ == "__main__":
    fetch_articles_without_content()
