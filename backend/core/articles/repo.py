from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from core.common.utils.async_tools import run_sync


class ArticleRepository:

    ARTICLE_TABLE = "articles"

    def __init__(self, client: Any):
        self.client = client

    async def get_articles_base(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "publish_time.desc",
    ):
        """获取文章列表"""
        return await self.client.select(
            self.ARTICLE_TABLE,
            filters=filters,
            limit=limit,
            offset=offset,
            order=order_by,
        )

    async def get_articles(
        self,
        mp_id: Optional[str] = None,
        status: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "publish_at.desc",
    ):
        """根据公众号ID和状态获取文章列表"""
        filters = {}
        if mp_id is not None:
            filters["mp_id"] = mp_id
        if status is not None:
            filters["status"] = status

        return await self.client.select(
            self.ARTICLE_TABLE,
            filters=filters or None,
            limit=limit,
            offset=offset,
            order=order_by,
        )

    async def get_articles_by_mp_ids(
        self,
        mp_ids: List[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        """根据公众号ID列表获取文章"""
        return await self.client.select(
            self.ARTICLE_TABLE,
            filters={"mp_id": {"in": mp_ids}},
            limit=limit,
            offset=offset,
            order="publish_time.desc",
        )

    async def get_articles_by_id(
        self,
        article_id: str,
    ):
        """根据文章ID获取文章"""
        return await self.client.select(
            self.ARTICLE_TABLE, filters={"id": article_id}, limit=1
        )

    async def get_articles_by_time_range(
        self, start_time: datetime, end_time: datetime, limit: Optional[int] = None
    ):
        filters = {
            "publish_at": {"gte": start_time.isoformat(), "lte": end_time.isoformat()}
        }
        return await self.client.select(
            self.ARTICLE_TABLE, filters=filters, order="publish_at.desc", limit=limit
        )

    async def count_articles_base(self, filters: Optional[Dict] = None):
        """统计文章数量"""
        return await self.client.count(self.ARTICLE_TABLE, filters=filters)

    async def count_articles(self, mp_id=None, status=None):
        """统计文章数量"""
        filters = {}
        if mp_id is not None:
            filters["mp_id"] = mp_id
        if status is not None:
            filters["status"] = status
        return await self.client.count(self.ARTICLE_TABLE, filters=filters)

    async def search_articles(self, keyword: str, limit: int = 100):
        """搜索文章"""
        # 格式化搜索关键词
        words = keyword.replace("-", " ").replace("|", " ").split(" ")
        words = [word.strip() for word in words if word.strip()]
        if not words:
            return []

        # 构建OR条件搜索
        filters = {"or": []}
        for word in words:
            filters["or"].append({"title": {"like": f"%{word}%"}})

        return await self.client.select(
            self.ARTICLE_TABLE, filters=filters, limit=limit, order="publish_time.desc"
        )

    # TODO: 统一文章列表查询接口, 支持 search + 过滤条件
    # async def list_articles(
    #     self,
    #     mp_id: Optional[str] = None,
    #     status: Optional[int] = None,
    #     search: Optional[str] = None,
    #     limit: Optional[int] = None,
    #     offset: Optional[int] = None,
    #     order_by: str = "publish_at.desc",
    # ) -> tuple[list[dict[str, Any]], int]:
    #     """
    #     统一的文章列表查询：
    #     - 支持按 mp_id + status 过滤
    #     - 支持搜索（search 一旦有值，将忽略 mp_id/status 过滤，与当前 API 行为保持一致）
    #     - 返回 (articles, total)
    #     """
    #     if search:
    #         # 搜索模式：沿用原先 search_articles 的语义
    #         if limit is not None and offset is not None:
    #             raw = await self.search_articles(search, limit=limit + offset)
    #             total = len(raw)
    #             articles = raw[offset : offset + limit]
    #         else:
    #             raw = await self.search_articles(search)
    #             total = len(raw)
    #             articles = raw
    #         return articles, total
    #
    #     # 非搜索模式：按 mp_id + status 过滤
    #     filters: dict[str, Any] = {}
    #     if mp_id is not None:
    #         filters["mp_id"] = mp_id
    #     if status is not None:
    #         filters["status"] = status
    #
    #     articles = await self.client.select(
    #         self.ARTICLE_TABLE,
    #         filters=filters or None,
    #         limit=limit,
    #         offset=offset,
    #         order=order_by,
    #     )
    #     total = await self.count_articles(mp_id=mp_id, status=status)
    #     return articles, total

    async def clean_expired_articles(self, days: int = 15):
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        expired_articles = await self.client.select(
            self.ARTICLE_TABLE,
            filters={"publish_at": {"lt": cutoff_date.isoformat()}, "status": 1},
        )

        if not expired_articles:
            return 0

        article_ids = [article["id"] for article in expired_articles]
        await self.client.delete("article_tags", {"article_id": {"in": article_ids}})
        deleted_articles = await self.client.delete(
            self.ARTICLE_TABLE, {"id": {"in": article_ids}}
        )
        return len(deleted_articles)

    async def delete_article(self, article_id: str):
        """删除文章"""
        return await self.client.delete(self.ARTICLE_TABLE, {"id": article_id})

    async def create_article(self, article_data: Dict):
        """创建文章"""
        return await self.client.insert(self.ARTICLE_TABLE, article_data)

    async def update_article(self, article_id: str, article_data: Dict):
        """更新文章"""
        article_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return await self.client.update(
            self.ARTICLE_TABLE, article_data, filters={"id": article_id}
        )

    #! 同步接口封装，用于jobs

    def sync_create_article(self, article_data: Dict):
        """同步创建文章（用于兼容同步代码）"""
        return run_sync(self.create_article(article_data))

    def sync_update_article(self, article_id: str, article_data: Dict):
        """同步更新文章（用于兼容同步代码）"""
        return run_sync(self.update_article(article_id, article_data))

    def sync_count_articles(self, filters: Optional[Dict] = None):
        """同步统计文章数量（用于兼容同步代码）"""
        return run_sync(self.count_articles_base(filters=filters))

    def sync_get_articles(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "publish_time.desc",
    ):
        """同步获取文章列表（用于兼容同步代码）"""
        return run_sync(
            self.get_articles_base(
                filters=filters, limit=limit, offset=offset, order_by=order_by
            )
        )

    def sync_delete_article(self, article_id: str):
        """同步删除文章（用于兼容同步代码）"""
        return run_sync(self.delete_article(article_id))


