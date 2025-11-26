from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any


class EventsRepository:

    EVENT_TABLE = "events"

    def __init__(self, client: Any):
        self.client = client

    async def get_events(
        self,
        article_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        """获取事件列表"""
        filters: Dict[str, Any] = {}
        if article_id is not None:
            filters["article_id"] = article_id

        return await self.client.select(
            self.EVENT_TABLE,
            filters=filters or None,
            limit=limit,
            offset=offset,
        )

    async def get_event_by_id(self, event_id: str):
        """根据 ID 获取事件"""
        result = await self.client.select(
            self.EVENT_TABLE,
            filters={"id": event_id},
            limit=1,
        )
        return result[0] if result else None

    async def create_event(self, event_data: Dict):
        """创建事件"""
        return await self.client.insert(self.EVENT_TABLE, event_data)

    async def update_event(self, event_id: str, event_data: Dict):
        """更新事件"""
        return await self.client.update(
            self.EVENT_TABLE, event_data, filters={"id": event_id}
        )

    async def delete_event(self, event_id: str):
        """删除事件"""
        result = await self.client.delete(self.EVENT_TABLE, filters={"id": event_id})
        return bool(result)

    async def upsert_event_from_article(self, article_data: Dict):
        """从文章数据创建或更新事件"""
        # 检查是否已存在
        existing_events = await self.client.select(
            self.EVENT_TABLE,
            filters={"source_id": article_data["id"], "source_type": "article"},
        )

        event_data = {
            "title": article_data.get("title", ""),
            "content": article_data.get("content", ""),
            "event_type": "article_published",
            "source_id": article_data.get("id"),
            "source_type": "article",
            "metadata": {
                "mp_id": article_data.get("mp_id"),
                "pic_url": article_data.get("pic_url"),
                "url": article_data.get("url"),
                "publish_time": article_data.get("publish_time"),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if existing_events:
            # 更新现有事件
            existing = existing_events[0]
            return await self.client.update(
                self.EVENT_TABLE, event_data, filters={"id": existing["id"]}
            )
        else:
            # 创建新事件
            event_data["created_at"] = datetime.now(timezone.utc).isoformat()
            return await self.client.insert(self.EVENT_TABLE, event_data)
