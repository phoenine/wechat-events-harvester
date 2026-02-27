"""Supabase 集成包。

导入约定：
- 业务代码请优先直接从子模块导入（client/auth/storage/auth_session_store）。
- 包级仅暴露 settings，避免形成过宽的聚合导出面。
"""

from core.integrations.supabase.settings import settings

__all__ = ["settings"]

