from typing import Optional
from pydantic import BaseModel


class MessageTask(BaseModel):
    id: str
    message_type: int
    name: str
    message_template: str
    web_hook_url: str
    mps_id: str
    cron_exp: str = "* * 1 * *"
    status: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
