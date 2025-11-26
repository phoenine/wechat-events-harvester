from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from core.utils.async_tools import run_sync


class UserRepository:

    USE_TABLE = "users"

    def __init__(self, client: Any):
        self.client = client

    async def get_users(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        return await self.client.select(
            self.USE_TABLE, filters=filters or None, limit=limit, offset=offset
        )

    async def get_user_by_username(self, username: str):
        users = await self.client.select(self.USE_TABLE, filters={"username": username})
        return users[0] if users else None

    async def get_user_by_id(self, user_id: str):
        users = await self.client.select(self.USE_TABLE, filters={"id": user_id})
        return users[0] if users else None

    async def create_user(self, user_data: Dict):
        return await self.client.insert(self.USE_TABLE, user_data)

    async def update_user(self, user_id: str, user_data: Dict):
        return await self.client.update(
            self.USE_TABLE, user_data, filters={"id": user_id}
        )

    async def update_user_avatar(self, user_id: str, avatar_url: str):
        """更新用户头像"""
        update_data = {
            "avatar": avatar_url,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return await self.client.update(
            self.USE_TABLE,
            update_data,
            filters={"id": user_id},
        )

    async def count_users(self, filters: Optional[Dict] = None):
        """统计用户数量"""
        return await self.client.count(self.USE_TABLE, filters=filters or None)

    async def create_user_profile(self, user_id: str, username: str):
        """创建用户资料"""
        profile_data = {
            "id": user_id,
            "username": username,
            "role": "user",
            "permissions": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
        }
        return await self.client.insert(self.USE_TABLE, profile_data)

    # TODO: 同步方法优化，后续删除

    def sync_create_user(self, user_data: Dict):
        """同步创建用户（用于兼容同步代码）"""
        return run_sync(self.create_user(user_data))
