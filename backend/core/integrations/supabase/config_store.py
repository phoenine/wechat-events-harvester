from __future__ import annotations

from typing import Any, Optional

from core.common.log import logger
from core.integrations.supabase.client import supabase_client
from core.integrations.supabase.settings import settings


class ConfigStore:
    """运行时配置存储（Supabase）"""

    TABLE_NAME = "config_managements"

    def __init__(self):
        self.client = supabase_client

    def available(self) -> bool:
        return bool(settings.url and settings.service_key)

    async def list(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        if not self.available():
            return []
        try:
            return await self.client.select(
                self.TABLE_NAME,
                columns="config_key,config_value,description,updated_at,created_at",
                order="updated_at",
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"读取配置列表失败: {e}")
            raise

    async def count(self) -> int:
        if not self.available():
            return 0
        return int(await self.client.count(self.TABLE_NAME))

    async def get(self, config_key: str) -> Optional[dict[str, Any]]:
        if not self.available():
            return None
        rows = await self.client.select(
            self.TABLE_NAME,
            filters={"config_key": config_key},
            columns="config_key,config_value,description,updated_at,created_at",
            limit=1,
        )
        return rows[0] if rows else None

    async def create(self, config_key: str, config_value: str, description: str = "") -> dict[str, Any]:
        if not self.available():
            raise RuntimeError("Supabase 不可用")
        row = await self.client.insert(
            self.TABLE_NAME,
            {
                "config_key": config_key,
                "config_value": config_value,
                "description": description,
            },
        )
        return row or {}

    async def update(self, config_key: str, config_value: str, description: Optional[str] = None) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError("Supabase 不可用")
        payload: dict[str, Any] = {"config_value": config_value}
        if description is not None:
            payload["description"] = description
        rows = await self.client.update(
            self.TABLE_NAME,
            payload,
            filters={"config_key": config_key},
        )
        return rows[0] if rows else {}

    async def delete(self, config_key: str) -> bool:
        if not self.available():
            return False
        rows = await self.client.delete(
            self.TABLE_NAME,
            filters={"config_key": config_key},
        )
        return bool(rows)


config_store = ConfigStore()

