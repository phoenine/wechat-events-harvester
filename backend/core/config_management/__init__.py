"""配置管理领域模块。"""

from core.integrations.supabase import supabase_client
from core.config_management.repo import ConfigRepository
from core.config_management.model import ConfigManagement


config_repo = ConfigRepository(supabase_client)

__all__ = ["config_repo", "ConfigManagement"]
