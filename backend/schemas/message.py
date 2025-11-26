from pydantic import BaseModel
from typing import Optional, Any


class MessageTaskCreate(BaseModel):
    message_template: str
    web_hook_url: str
    mps_id: str = ""
    name: str = ""
    message_type: int = 0
    cron_exp: str = ""
    status: Optional[int] = 0