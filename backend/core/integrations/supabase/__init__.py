import os
from typing import Dict
from dataclasses import dataclass


@dataclass(frozen=True)
class BucketConfig:
    name: str
    path: str
    expires: int


@dataclass(frozen=True)
class SupabaseSettings:
    url: str
    anon_key: str
    service_key: str
    buckets: Dict[str, BucketConfig]


def _load_settings() -> SupabaseSettings:
    buckets = {
        "qr": BucketConfig(
            name=os.getenv("STORAGE_QR_BUCKET", "qr"),
            path=os.getenv("SUPABASE_QR_PATH", "wx/{uuid}.png"),
            expires=int(os.getenv("SUPABASE_QR_SIGN_EXPIRES", "120")),
        ),
        "avatar": BucketConfig(
            name=os.getenv("STORAGE_AVATAR_BUCKET", "avatar"),
            path=os.getenv("SUPABASE_AVATAR_PATH", "avatars/{uuid}.png"),
            expires=0,
        ),
        "articles": BucketConfig(
            name=os.getenv("STORAGE_BACKUP_BUCKET", "articles"),
            path=os.getenv("SUPABASE_ARTICLE_IMAGE_PATH", "articles/{article_name}/{filename}"),
            expires=0,
        ),
    }

    return SupabaseSettings(
        url=os.getenv("SUPABASE_URL", "").rstrip("/"),
        anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        service_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
        buckets=buckets,
    )


settings = _load_settings()

from core.integrations.supabase.client import supabase_client, SupabaseClient
from core.integrations.supabase.auth import (
    auth_manager,
    SupabaseAuthManager,
    get_current_user,
    get_current_user_optional,
)
from core.integrations.supabase.storage import (
    supabase_storage_qr,
    supabase_storage_avatar,
    supabase_storage_articles,
    SupabaseStorage,
)
from core.integrations.supabase.database import db_manager, DatabaseManager

__all__ = [
    "supabase_client",
    "SupabaseClient",
    "auth_manager",
    "SupabaseAuthManager",
    "get_current_user",
    "get_current_user_optional",
    "supabase_storage_qr",
    "supabase_storage_avatar",
    "supabase_storage_articles",
    "SupabaseStorage",
    "db_manager",
    "DatabaseManager",
]
