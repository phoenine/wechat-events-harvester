from __future__ import annotations
from core.config import print_error
from core.wx.base import WxGatherHooks


def build_wx_gather_hooks() -> WxGatherHooks:
    """构建 WxGather 的默认 hooks 实现。"""

    def _on_update_mps(mp_id: str, mp: dict) -> None:
        """更新公众号同步状态/时间（DB 副作用）。"""
        try:
            from datetime import datetime
            import time
            from core.repositories import feed_repo

            current_time = int(time.time())
            update_data = {
                "sync_time": current_time,
                "updated_at": datetime.now().isoformat(),
            }
            if isinstance(mp, dict):
                if mp.get("update_time"):
                    update_data["update_time"] = mp.get("update_time")
                if mp.get("status") is not None:
                    update_data["status"] = mp.get("status")

            feed_repo.sync_update_feed(mp_id, update_data)
        except Exception:
            return

    def _on_over(articles: list, mp_id: str | None) -> None:
        """抓取完成后的收尾副作用（如 RSS 缓存清理）。"""
        try:
            from core.rss import RSS

            if mp_id:
                RSS().clear_cache(mp_id=mp_id)
        except Exception:
            pass

    def _on_error(error: str, code: str | None, ctx: dict) -> None:
        """错误处理副作用（仅对登录失效做处理）。"""
        if code != "Invalid Session":
            return

        # 1) 清理 driver 会话（best-effort）
        try:
            from driver.wx_service import clear_session

            clear_session()
        except Exception:
            pass

        # 2) 清理任务队列（best-effort）
        try:
            from core.utils.task_queue import TaskQueue

            TaskQueue.delete_queue()
        except Exception:
            pass

        # 3) 发送登录失效通知（best-effort）
        try:
            import threading
            from jobs.failauth import send_wx_code

            threading.Thread(
                target=send_wx_code,
                args=("公众号平台登录失效,请重新登录",),
            ).start()
        except Exception:
            print_error("公众号平台登录失效,请重新登录，且发送通知失败")

    return WxGatherHooks(
        on_update_mps=_on_update_mps,
        on_over=_on_over,
        on_error=_on_error,
    )
