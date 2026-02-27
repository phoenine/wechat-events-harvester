"""用户资料领域模块。"""

from core.integrations.supabase.client import supabase_client
from core.profiles.repo import ProfilesRepository
from core.profiles.model import Profile


profile_repo = ProfilesRepository(supabase_client)

__all__ = ["profile_repo", "Profile"]
