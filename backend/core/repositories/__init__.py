from core.supabase.database import db_manager
from .user import UserRepository
from .articles import ArticleRepository
from .tags import TagRepository
from .events import EventsRepository
from .message import MessageRepository
from .config import ConfigRepository
from .feeds import FeedRepository

# 全局单例 SupabaseClient 实例
client = db_manager

user_repo = UserRepository(client)
article_repo = ArticleRepository(client)
tag_repo = TagRepository(client)
event_repo = EventsRepository(client)
message_repo = MessageRepository(client)
config_repo = ConfigRepository(client)
feed_repo = FeedRepository(client)


__all__ = [
    "user_repo",
    "article_repo",
    "tag_repo",
    "event_repo",
    "message_repo",
    "config_repo",
    "feed_repo",
]
