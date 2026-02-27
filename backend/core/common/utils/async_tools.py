import asyncio
import threading
from typing import TypeVar, Awaitable

T = TypeVar("T")

def run_sync(coro: Awaitable[T]) -> T:
    """在同步上下文中执行协程。

    - 当前线程无运行中的事件循环：直接新建 loop 执行
    - 当前线程已有运行中的事件循环：切到子线程执行，避免嵌套 loop 报错
    """
    try:
        asyncio.get_running_loop()
        has_running_loop = True
    except RuntimeError:
        has_running_loop = False

    if not has_running_loop:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    result: dict[str, T] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result["value"] = loop.run_until_complete(coro)
        except BaseException as e:
            error["err"] = e
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()

    if "err" in error:
        raise error["err"]
    return result["value"]
