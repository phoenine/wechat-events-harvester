from pydantic import BaseModel
from typing import Any, Dict


class UserCredentials(BaseModel):
    """用户凭据模型（用户名/密码登录）"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
