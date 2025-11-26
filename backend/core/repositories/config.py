from datetime import datetime, timezone
from typing import Optional, Dict, Any
from core.utils.async_tools import run_sync


class ConfigRepository:
    """配置与配置管理仓储，基于 Supabase 实现"""

    CONFIG_MANAGEMENT_TABLE = "config_management"

    def __init__(self, client: Any):
        self.client = client

    async def get_configs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "config_key.asc",
    ):
        """获取配置列表"""
        return await self.client.select(
            self.CONFIG_MANAGEMENT_TABLE,
            filters=filters,
            order=order_by,
        )

    async def get_config_by_key(self, key: str):
        """根据key获取配置"""
        configs = await self.client.select(
            self.CONFIG_MANAGEMENT_TABLE,
            filters={"config_key": key},
        )
        return configs[0] if configs else None

    async def set_config(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
    ) -> Any:
        """设置配置"""
        now = datetime.now(timezone.utc).isoformat()
        config_data: Dict[str, Any] = {
            "config_key": key,
            "config_value": value,
            "updated_at": now,
        }
        if description is not None:
            config_data["description"] = description

        # 检查是否已存在
        existing = await self.get_config_by_key(key)
        if existing:
            return await self.client.update(
                self.CONFIG_MANAGEMENT_TABLE,
                config_data,
                filters={"config_key": key},
            )
        else:
            config_data["created_at"] = now
            return await self.client.insert(
                self.CONFIG_MANAGEMENT_TABLE,
                config_data,
            )

    async def delete_config(self, key: str) -> bool:
        """删除配置（基于 config_management 表）"""
        result = await self.client.delete(
            self.CONFIG_MANAGEMENT_TABLE,
            filters={"config_key": key},
        )
        return bool(result)

    # ===== 同步包装 =====

    def sync_get_configs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "config_key.asc",
    ):
        """同步获取配置列表（用于兼容同步代码）"""
        return run_sync(self.get_configs(filters=filters, order_by=order_by))

    def sync_set_config(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
    ):
        """同步设置配置（用于兼容同步代码）"""
        return run_sync(self.set_config(key, value, description))
