from typing import Optional
from pydantic import BaseModel

class ConfigManagement(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None
