from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from core.utils.async_tools import run_sync


class FeedRepository:

    FEED_TABLE = "feeds"
    def __init__(self, client: Any):
        self.client = client

    async def get_feeds(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at.desc",
    ):
        """获取订阅源列表（通用过滤）"""
        return await self.client.select(
            self.FEED_TABLE, filters=filters, limit=limit, offset=offset, order=order_by
        )

    async def get_feeds_by_status(
        self,
        status: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at.desc",
    ):
        """根据状态获取订阅源列表（便捷方法）"""
        filters = {"status": status}
        return await self.get_feeds(
            filters=filters, limit=limit, offset=offset, order_by=order_by
        )

    async def get_feed_by_id(self, feed_id: str):
        """根据ID获取订阅源"""
        feeds = await self.client.select(self.FEED_TABLE, filters={"id": feed_id})
        return feeds[0] if feeds else None

    async def get_feeds_by_ids(self, feed_ids: List[str]):
        """根据ID列表获取公众号"""
        return await self.client.select(self.FEED_TABLE, filters={"id": {"in": feed_ids}})

    async def get_feed_by_faker_id(self, faker_id: str):
        """根据faker_id获取订阅源"""
        feeds = await self.client.select(self.FEED_TABLE, filters={"faker_id": faker_id})
        return feeds[0] if feeds else None

    async def count_feeds(self, filters: Optional[Dict] = None):
        """统计订阅源数量"""
        return await self.client.count(self.FEED_TABLE, filters=filters)

    async def create_feed(self, feed_data: Dict):
        """创建订阅源"""
        return await self.client.insert(self.FEED_TABLE, feed_data)

    async def update_feed(self, feed_id: str, feed_data: Dict):
        """更新订阅源"""
        return await self.client.update(self.FEED_TABLE, feed_data, filters={"id": feed_id})

    async def delete_feed(self, feed_id: str):
        """删除订阅源"""
        return await self.client.delete(
            self.FEED_TABLE,
            filters={"id": feed_id},
        )

    #! 同步方法，用于兼容同步代码jobs

    def sync_get_feeds_by_ids(self, feed_ids: List[str]):
        """同步根据ID列表获取公众号(用于兼容同步代码)"""
        return run_sync(self.get_feeds_by_ids(feed_ids))

    def sync_update_feed(self, feed_id: str, feed_data: Dict):
        """同步更新订阅源（用于兼容同步代码）"""
        return run_sync(self.update_feed(feed_id, feed_data))

    def sync_count_feeds(self, filters: Optional[Dict] = None):
        """同步统计订阅源数量（用于兼容同步代码）"""
        return run_sync(self.count_feeds(filters=filters))

    def sync_get_feeds(self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at.desc",
    ):
        """同步获取订阅源列表（用于兼容同步代码）"""
        return run_sync(
            self.get_feeds(
                filters=filters, limit=limit, offset=offset, order_by=order_by
            )
        )
