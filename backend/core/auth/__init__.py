"""认证领域模块。"""

from core.integrations.supabase import supabase_client
from core.auth.repo import AuthRepository
from core.auth.model import UserCredentials, TokenResponse


auth_repo = AuthRepository(supabase_client)

__all__ = ["auth_repo", "UserCredentials", "TokenResponse"]
