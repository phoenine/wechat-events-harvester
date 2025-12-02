from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Profile(BaseModel):
    """ 用户扩展资料模型 """

    user_id: str = Field(..., description="Supabase Auth 用户 ID")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像 URL")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
