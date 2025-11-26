import asyncio
from typing import TypeVar, Awaitable

T = TypeVar("T")

def run_sync(coro: Awaitable[T]) -> T:
    """在新的事件循环中运行异步协程（用于兼容同步代码）"""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)
