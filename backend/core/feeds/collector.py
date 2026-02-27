from typing import Any, Callable, Optional

from core.integrations.wx import create_gather
from core.common.log import logger


def _feed_value(feed: Any, key: str) -> Any:
    if isinstance(feed, dict):
        return feed.get(key)
    return getattr(feed, key, None)


def collect_feed_articles(
    feed: Any,
    *,
    on_article: Optional[Callable[..., Any]] = None,
    on_finish: Optional[Callable[..., Any]] = None,
    start_page: int = 0,
    max_page: int = 1,
    interval: Optional[int] = None,
) -> dict[str, Any]:
    """采集单个公众号文章并返回结果。"""
    faker_id = _feed_value(feed, "faker_id")
    mp_id = _feed_value(feed, "id")
    mp_name = _feed_value(feed, "mp_name")

    if not faker_id:
        raise ValueError("公众号缺少 faker_id，无法采集")

    wx = create_gather()
    try:
        wx.get_Articles(
            faker_id,
            Mps_id=mp_id,
            Mps_title=mp_name,
            CallBack=on_article,
            Over_CallBack=on_finish,
            start_page=start_page,
            MaxPage=max_page,
            interval=interval,
        )
    except Exception as e:
        logger.error(f"采集公众号[{mp_name or mp_id}]失败: {e}")
        raise

    return {
        "feed_id": mp_id,
        "feed_name": mp_name,
        "articles": wx.articles,
        "count": wx.all_count(),
    }
