import asyncio
import time
import os

from dotenv import load_dotenv
load_dotenv()

from core.supabase.auth import pwd_context
from core.repositories import user_repo
from core.print import print_info, print_error


async def init_user():
    try:
        username, password = os.getenv("USERNAME", "admin"), os.getenv(
            "PASSWORD", "admin@123"
        )

        user_data = {
            "id": "0",
            "username": username,
            "password_hash": pwd_context.hash(password),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        await user_repo.create_user(user_data)
        print_info(f"初始化用户成功,请使用以下凭据登录：{username}")
    except Exception as e:
        print_error(f"Init error: {str(e)}")


def sync_models():
    """同步模型到表结构"""
    print_info("使用Supabase, 表结构通过迁移管理, 跳过模型同步")
    pass


async def init():
    sync_models()
    await init_user()


if __name__ == "__main__":
    asyncio.run(init())
