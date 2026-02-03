"""标签领域模块。"""

from core.integrations.supabase import supabase_client
from core.tags.repo import TagRepository
from core.tags.model import Tags


tag_repo = TagRepository(supabase_client)

__all__ = ["tag_repo", "Tags"]
