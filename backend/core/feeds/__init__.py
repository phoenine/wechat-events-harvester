"""公众号/订阅源领域模块。"""

from core.integrations.supabase import supabase_client
from core.feeds.repo import FeedRepository
from core.feeds.model import Feed


feed_repo = FeedRepository(supabase_client)

__all__ = ["feed_repo", "Feed"]
