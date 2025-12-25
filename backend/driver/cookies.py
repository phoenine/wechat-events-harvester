import time
from typing import Any, Iterable, Optional
from core.print import print_warning


def expire(cookies: Any, *, cookie_name: str = "slave_sid") -> Optional[dict]:
    """提取cookie的过期时间信息"""

    if cookies is None:
        return None

    # 归一化输入，确保cookie_items为可迭代的cookie字典列表
    cookie_items: Iterable[Any]
    if isinstance(cookies, list) or isinstance(cookies, tuple):
        cookie_items = cookies
    elif isinstance(cookies, dict):
        # 兼容单个cookie字典，包装成列表
        cookie_items = [cookies]
    else:
        raise TypeError("cookies 参数必须是 cookie dict 或 cookie dict 列表")

    # 遍历cookie列表，查找匹配cookie_name的cookie
    for cookie in cookie_items:
        if not isinstance(cookie, dict):
            continue

        name = cookie.get("name")
        if name != cookie_name:
            continue

        # Playwright cookie通常使用'expires'字段，类型为unix时间戳(float或int)。
        # 有些来源可能存储为字符串。
        if "expires" not in cookie:
            return None

        # 尝试将'expires'字段转换为浮点数，若失败则打印警告并返回None
        try:
            expiry_time = float(cookie.get("expires"))
        except (TypeError, ValueError):
            # NOTE: 此处存在副作用，打印无效时间戳，调用方需注意
            print_warning(f"{cookie_name} 的过期时间戳无效: {cookie.get('expires')}")
            return None

        # 计算剩余时间，若已过期返回None
        remaining_time = expiry_time - time.time()
        if remaining_time <= 0:
            return None

        return {
            "expiry_timestamp": expiry_time,
            "remaining_seconds": int(remaining_time),
            "expiry_time": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(expiry_time)
            ),
        }

    return None
