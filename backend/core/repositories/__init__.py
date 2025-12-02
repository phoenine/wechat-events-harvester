from core.supabase import supabase_client
from .articles import ArticleRepository
from .tags import TagRepository
from .events import EventsRepository
from .message import MessageRepository
from .config import ConfigRepository
from .feeds import FeedRepository
from .profiles import ProfilesRepository

# 全局单例 SupabaseClient 实例
client = supabase_client

article_repo = ArticleRepository(client)
tag_repo = TagRepository(client)
event_repo = EventsRepository(client)
message_repo = MessageRepository(client)
config_repo = ConfigRepository(client)
feed_repo = FeedRepository(client)
profile_repo = ProfilesRepository(client)


__all__ = [
    "article_repo",
    "tag_repo",
    "event_repo",
    "message_repo",
    "config_repo",
    "feed_repo",
    "profile_repo",
]
