import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

from core.integrations.supabase.auth import auth_manager
from core.common.print import print_info, print_error


async def init_user():
    """使用 Supabase Auth 初始化管理员账户"""

    username: str = os.getenv("USERNAME", "admin@example.com")
    password: str = os.getenv("PASSWORD", "admin@123")

    try:
        result = await auth_manager.sign_up(
            email=username,
            password=password,
            user_metadata={"role": "admin"},
        )

        print_info(f"初始化 Supabase Auth 用户成功, 请使用以下凭据登录：{username}")
    except Exception as e:
        msg = str(e)
        if "User already registered" in msg or "already exists" in msg:
            print_info(f"Supabase Auth 中已存在用户：{username}，跳过创建")
        else:
            print_error(f"Init error: {msg}")


def sync_models():
    """同步模型到表结构"""
    print_info("使用Supabase, 表结构通过迁移管理, 跳过模型同步")
    pass


async def init():
    sync_models()
    await init_user()


if __name__ == "__main__":
    asyncio.run(init())
