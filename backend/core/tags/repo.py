from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class TagRepository:

    TAG_TABLE = "tags"
    FEED_TABLE = "feeds"

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _as_tag_int(tag_id: str | int) -> int:
        return int(str(tag_id).strip())

    async def get_tags(self, limit: Optional[int] = None, offset: Optional[int] = None):
        """获取所有标签"""
        return await self.client.select(
            self.TAG_TABLE, limit=limit, offset=offset, order="name.asc"
        )

    async def get_feed_ids_by_tag(self, tag_id: str) -> List[str]:
        """获取标签关联的公众号ID列表。"""
        tag_id_int = self._as_tag_int(tag_id)
        rows = await self.client.select(
            self.FEED_TABLE,
            filters={"tag_id": tag_id_int},
            order="created_at.asc",
        )
        return [str(r.get("id")) for r in rows if r.get("id")]

    async def replace_feed_tags(self, tag_id: str, feed_ids: List[str]):
        """按标签替换公众号关联关系（一对多：feeds.tag_id）。"""
        tag_id_int = self._as_tag_int(tag_id)
        # 先解绑当前标签下的所有 feed
        await self.client.update(
            self.FEED_TABLE,
            {"tag_id": None},
            filters={"tag_id": tag_id_int},
        )
        ids = [str(i).strip() for i in (feed_ids or []) if str(i).strip()]
        if not ids:
            return []
        existing_rows = await self.client.select(
            self.FEED_TABLE,
            filters={"id": {"in": sorted(set(ids))}},
            columns="id",
        )
        existing_ids = {str(r.get("id")) for r in existing_rows if r.get("id")}
        if not existing_ids:
            raise ValueError("所选公众号ID不存在，无法绑定标签")
        updated = []
        for fid in sorted(existing_ids):
            rows = await self.client.update(
                self.FEED_TABLE,
                {"tag_id": tag_id_int},
                filters={"id": fid},
            )
            if rows:
                updated.extend(rows)
        return updated

    async def count_tags(self, filters: Optional[Dict] = None):
        """统计标签数量"""
        return await self.client.count(self.TAG_TABLE, filters=filters)

    async def get_tag_by_id(self, tag_id: str):
        """根据ID获取标签"""
        tags = await self.client.select(self.TAG_TABLE, filters={"id": tag_id})
        return tags[0] if tags else None

    async def get_tag_by_name(self, name: str):
        """根据名称获取标签"""
        tags = await self.client.select(self.TAG_TABLE, filters={"name": name})
        return tags[0] if tags else None

    async def create_tag(self, tag_data: Dict):
        """创建标签"""
        return await self.client.insert(self.TAG_TABLE, tag_data)

    async def update_tag(self, tag_id: str, tag_data: Dict):
        """更新标签"""
        return await self.client.update(
            self.TAG_TABLE, tag_data, filters={"id": tag_id}
        )

    async def delete_tag(self, tag_id: str):
        """删除标签"""
        tag_id_int = self._as_tag_int(tag_id)
        await self.client.update(
            self.FEED_TABLE,
            {"tag_id": None},
            filters={"tag_id": tag_id_int},
        )
        result = await self.client.delete(self.TAG_TABLE, filters={"id": tag_id})
        return bool(result)
