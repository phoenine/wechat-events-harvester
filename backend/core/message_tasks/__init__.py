"""消息任务领域模块。"""

from core.integrations.supabase import supabase_client
from core.message_tasks.repo import MessageRepository
from core.message_tasks.model import MessageTask
from core.message_tasks.log_model import MessageTask as MessageTaskLog


message_repo = MessageRepository(supabase_client)

__all__ = ["message_repo", "MessageTask", "MessageTaskLog"]
