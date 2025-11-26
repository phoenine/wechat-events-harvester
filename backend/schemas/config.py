from pydantic import BaseModel
from typing import Optional


class ConfigManagementCreate(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None