from typing import Any, Dict, Optional


class ProfilesRepository:
    """profiles 表仓储类"""

    TABLE_NAME = "profiles"

    def __init__(self, client: Any) -> None:
        """接收一个 Supabase v2 Client 实例"""
        self.client = client

    def _table(self):
        """获取 profiles 表的查询构建器"""

        return self.client.table(self.TABLE_NAME)

    async def get_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据 Supabase Auth 的 user_id 获取 profile 记录"""

        table = self._table()
        query = table.select("*").eq("user_id", user_id).limit(1)
        resp = await query.execute()

        data = getattr(resp, "data", None)
        if not data:
            return None

        return data[0]

    async def update_avatar(self, user_id: str, avatar_url: str) -> Dict[str, Any]:
        """更新（或插入）用户头像 URL"""

        table = self._table()
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "avatar_url": avatar_url,
        }

        # 使用 upsert 以 user_id 作为冲突键实现插入或更新
        query = table.upsert(payload, on_conflict="user_id").select("*").limit(1)

        resp = await query.execute()
        data = getattr(resp, "data", None)
        if not data:
            return payload

        return data[0]
