from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class TagRepository:

    TAG_TABLE = "tags"

    def __init__(self, client: Any):
        self.client = client

    async def get_tags(self, limit: Optional[int] = None, offset: Optional[int] = None):
        """获取所有标签"""
        return await self.client.select(
            self.TAG_TABLE, limit=limit, offset=offset, order="name.asc"
        )

    async def get_articles_by_tags(
        self, tag_ids: List[int], limit: Optional[int] = None
    ):
        """根据标签获取文章"""
        # 先获取文章标签关联
        article_tags = await self.client.select(
            "article_tags", filters={"tag_id": {"in": tag_ids}}
        )

        if not article_tags:
            return []

        article_ids = [at["article_id"] for at in article_tags]

        # 再获取对应的文章
        return await self.client.select(
            "articles",
            filters={"id": {"in": article_ids}},
            order="publish_at.desc",
            limit=limit,
        )

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
        result = await self.client.delete(self.TAG_TABLE, filters={"id": tag_id})
        return bool(result)
