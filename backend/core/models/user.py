from typing import Optional
from pydantic import BaseModel



class User(BaseModel):
    id: str
    username: str
    password_hash: str
    is_active: bool = True
    role: Optional[str] = None
    permissions: Optional[str] = None
    nickname: str = ""
    avatar: str = "/static/default-avatar.png"   #TODO 这里的路径需要修改
    email: str = ""
    mp_name: Optional[str] = None
    mp_cover: Optional[str] = None
    mp_intro: Optional[str] = None
    status: Optional[int] = None
    sync_time: Optional[str] = None
    update_time: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    faker_id: Optional[str] = None

    def verify_password(self, password: str) -> bool:
        from core.supabase.auth import pwd_context

        return pwd_context.verify(password, self.password_hash)
