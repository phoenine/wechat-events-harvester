"""活动领域模块。"""

from core.integrations.supabase.client import supabase_client
from core.events.repo import EventsRepository
from core.events.model import Events


event_repo = EventsRepository(supabase_client)

__all__ = ["event_repo", "Events"]
