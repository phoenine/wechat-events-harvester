from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List


class AuthRepository:
    """认证会话相关的仓储类，基于 Supabase 实现"""

    AUTH_TABLE = "auth_sessions"

    def __init__(self, client: Any):
        self.client = client

    async def create_auth_session(
        self, session_id: str, user_id: Optional[str] = None, expires_minutes: int = 2
    ):
        """创建认证会话"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_minutes)

        session_data: Dict[str, Any] = {
            "id": session_id,
            "status": "waiting",
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        if user_id:
            session_data["user_id"] = user_id

        return await self.client.insert(self.AUTH_TABLE, session_data)

    async def update_auth_session(self, session_id: str, **kwargs):
        """更新认证会话"""
        kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
        return await self.client.update(self.AUTH_TABLE, kwargs, {"id": session_id})

    async def get_auth_session(self, session_id: str):
        """获取认证会话"""
        sessions = await self.client.select(self.AUTH_TABLE, filters={"id": session_id})
        return sessions[0] if sessions else None

    async def write_auth_session_secret(
        self,
        session_id: str,
        token: str,
        cookies_str: str = "",
        expiry_ts: Optional[float] = None,
    ):
        """写入认证会话密钥（合并到 auth_sessions 表）"""
        now = datetime.now(timezone.utc).isoformat()
        secret_data: Dict[str, Any] = {
            "token": token,
            "cookies_str": cookies_str,
            "updated_at": now,
        }

        if expiry_ts is not None:
            secret_data["expiry"] = datetime.fromtimestamp(
                expiry_ts, tz=timezone.utc
            ).isoformat()

        # 将密钥信息直接更新到 auth_sessions 表中
        return await self.client.update(
            self.AUTH_TABLE,
            secret_data,
            {"id": session_id},
        )
