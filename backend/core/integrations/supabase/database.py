import os
import uuid
import psycopg2
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from core.common.log import logger



class DatabaseManager:
    """数据库管理器 - 负责认证会话相关操作"""

    def __init__(self):
        # 会话管理相关
        self.session_url = os.getenv("SUPABASE_DB_URL")
        self.user_id = os.getenv("SUPABASE_USER_ID")
        self.conn = None

    def _get_session_conn(self):
        """获取会话数据库连接"""
        if not self.session_url:
            return None
        try:
            if self.conn is None or getattr(self.conn, "closed", False):
                self.conn = psycopg2.connect(self.session_url)
                self.conn.autocommit = True
        except Exception as e:
            logger.error(f"创建会话数据库连接失败: {e}")
            self.conn = None
            return None
        return self.conn

    def valid_session_db(self):
        """检查会话数据库是否可用"""
        return bool(self.session_url)

    async def create_session(
        self, user_id: Optional[str] = None, expires_minutes: int = 2
    ):
        """创建认证会话"""
        if not self.valid_session_db():
            return None

        sid = str(uuid.uuid4())
        uid = user_id or self.user_id
        if not uid:
            return sid  # 返回生成的会话ID，但不落库

        try:
            conn = self._get_session_conn()
            if not conn:
                logger.error("会话数据库连接不可用，跳过持久化会话")
                return sid
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.auth_sessions (id, user_id, status, expires_at) VALUES (%s, %s, %s, %s)",
                    (
                        sid,
                        uid,
                        "waiting",
                        datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
                    ),
                )
            return sid
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return sid  # 仍然返回会话ID，但记录错误

    async def update_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        qr_path: Optional[str] = None,
        qr_signed_url: Optional[str] = None,
        expires_minutes: Optional[int] = None,
    ):
        """更新会话信息"""
        if not self.valid_session_db() or not session_id:
            return False

        sets = []
        vals = []
        if status:
            sets.append("status=%s")
            vals.append(status)
        if qr_path:
            sets.append("qr_path=%s")
            vals.append(qr_path)
        if qr_signed_url:
            sets.append("qr_signed_url=%s")
            vals.append(qr_signed_url)
        if expires_minutes is not None:
            sets.append("expires_at=%s")
            vals.append(datetime.now(timezone.utc) + timedelta(minutes=expires_minutes))
        if not sets:
            return False

        try:
            conn = self._get_session_conn()
            if not conn:
                logger.error("会话数据库连接不可用，跳过更新会话")
                return False
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE public.auth_sessions SET {', '.join(sets)} WHERE id=%s",
                    vals + [session_id],
                )
            return True
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return False

    def update_session_sync(
        self,
        session_id: str,
        status: Optional[str] = None,
        qr_path: Optional[str] = None,
        qr_signed_url: Optional[str] = None,
        expires_minutes: Optional[int] = None,
    ):
        if not self.valid_session_db() or not session_id:
            return False
        sets = []
        vals = []
        if status:
            sets.append("status=%s")
            vals.append(status)
        if qr_path:
            sets.append("qr_path=%s")
            vals.append(qr_path)
        if qr_signed_url:
            sets.append("qr_signed_url=%s")
            vals.append(qr_signed_url)
        if expires_minutes is not None:
            sets.append("expires_at=%s")
            vals.append(datetime.now(timezone.utc) + timedelta(minutes=expires_minutes))
        if not sets:
            return False
        try:
            conn = self._get_session_conn()
            if not conn:
                logger.error("会话数据库连接不可用，跳过更新会话")
                return False
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE public.auth_sessions SET {', '.join(sets)} WHERE id=%s",
                    vals + [session_id],
                )
            return True
        except Exception as e:
            logger.error(f"更新会话失败(sync): {e}")
            return False

    async def write_secret(
        self,
        session_id: str,
        token: str,
        cookies_str: str,
        expiry_ts: Optional[float] = None,
    ):
        """写入会话密钥"""
        if not self.valid_session_db() or not session_id:
            return False
        expires_at = (
            datetime.fromtimestamp(expiry_ts, tz=timezone.utc) if expiry_ts else None
        )
        try:
            conn = self._get_session_conn()
            if not conn:
                logger.error("会话数据库连接不可用，跳过写入会话密钥")
                return False
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO public.auth_session_secret (session_id, token, cookies_str, expiry)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (session_id) DO UPDATE SET
                       token=EXCLUDED.token, cookies_str=EXCLUDED.cookies_str, expiry=EXCLUDED.expiry""",
                    (session_id, token or "", cookies_str or "", expires_at),
                )
            return True
        except Exception as e:
            logger.error(f"写入会话密钥失败: {e}")
            return False

    def write_secret_sync(
        self,
        session_id: str,
        token: str,
        cookies_str: str,
        expiry_ts: Optional[float] = None,
    ):
        if not self.valid_session_db() or not session_id:
            return False
        expires_at = (
            datetime.fromtimestamp(expiry_ts, tz=timezone.utc) if expiry_ts else None
        )
        try:
            conn = self._get_session_conn()
            if not conn:
                logger.error("会话数据库连接不可用，跳过写入会话密钥")
                return False
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO public.auth_session_secret (session_id, token, cookies_str, expiry)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (session_id) DO UPDATE SET
                       token=EXCLUDED.token, cookies_str=EXCLUDED.cookies_str, expiry=EXCLUDED.expiry""",
                    (session_id, token or "", cookies_str or "", expires_at),
                )
            return True
        except Exception as e:
            logger.error(f"写入会话密钥失败(sync): {e}")
            return False


db_manager = DatabaseManager()
