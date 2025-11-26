from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from core.utils.async_tools import run_sync


class MessageRepository:

    MESSAGE_TABLE = "message_tasks"

    def __init__(self, client: Any):
        self.client = client

    async def get_message_tasks(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at.desc",
    ):
        """获取消息任务"""
        return await self.client.select(
            self.MESSAGE_TABLE,
            filters=filters,
            limit=limit,
            offset=offset,
            order=order_by,
        )

    async def get_message_task_by_id(self, task_id: str):
        """根据 ID 获取单个消息任务"""
        result = await self.client.select(
            self.MESSAGE_TABLE,
            filters={"id": task_id},
            limit=1,
        )
        return result[0] if result else None

    async def count_message_tasks(self, filters: Optional[Dict] = None):
        """统计消息任务数量"""
        return await self.client.count(self.MESSAGE_TABLE, filters=filters)

    async def create_message_task(self, task_data: Dict):
        """创建消息任务"""
        return await self.client.insert(self.MESSAGE_TABLE, task_data)

    async def update_message_task(self, task_id: str, task_data: Dict):
        """更新消息任务"""
        return await self.client.update(
            self.MESSAGE_TABLE, task_data, filters={"id": task_id}
        )

    async def delete_message_task(self, task_id: str):
        """删除消息任务"""
        result = await self.client.delete(self.MESSAGE_TABLE, filters={"id": task_id})
        return bool(result)

    #! 同步方法，用于兼容同步代码jobs

    def sync_get_message_tasks(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at.desc",
    ):
        """同步获取消息任务（用于兼容同步代码）"""
        return run_sync(
            self.get_message_tasks(
                filters=filters, limit=limit, offset=offset, order_by=order_by
            )
        )
