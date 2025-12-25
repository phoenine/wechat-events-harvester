from __future__ import annotations
from threading import Lock, Timer
from typing import Callable, Optional, Any
from core.print import print_error


class RefreshManager:
    """定时刷新管理器，负责定时执行刷新操作以保持会话活跃和校验状态"""

    def __init__(
        self,
        refresh_interval: int,
        get_controller: Callable[[], Any],
        is_logged_in: Callable[[], bool],
        on_refresh_success: Callable[[], None],
        on_expired: Callable[[], None],
        login_lock: Lock,
    ):
        self.refresh_interval = refresh_interval
        self._get_controller = get_controller
        self._is_logged_in = is_logged_in
        self._on_refresh_success = on_refresh_success
        self._on_expired = on_expired
        self._lock = login_lock
        self._timer: Optional[Timer] = None

    def stop(self):
        """停止刷新定时器"""
        try:
            t = self._timer
            if t is not None:
                t.cancel()
        except Exception:
            pass
        self._timer = None

    def _schedule_next(self):
        if self.refresh_interval <= 0:
            return
        # 仅允许一个 timer 存在，使用共享锁防止竞争
        with self._lock:
            # 先停止现有定时器，避免重复定时任务
            self.stop()
            timer = Timer(self.refresh_interval, self.tick)
            timer.daemon = True  # 守护线程，程序退出时自动结束
            self._timer = timer
            timer.start()

    def refresh_once(self):
        """执行一次刷新（不负责安排下一次）"""
        controller = self._get_controller()
        page = getattr(controller, "page", None) if controller is not None else None
        if not page:
            raise Exception("页面刷新失败")

        # 重新加载页面作为保活操作
        page.reload()
        # 刷新任务仅用于保活与校验，不应在这里重复启动/重置定时器
        self._on_refresh_success()

        # 简单粗略的有效性校验：检查 URL 中是否包含 "home"
        if "home" not in (page.url or ""):
            # 过期：外部统一处理状态与定时器
            self._on_expired()
            raise Exception("登录已经失效，请重新登录")

    def tick(self):
        """定时器回调：执行刷新并安排下一次"""
        # 关键前置条件：已登录且 controller 存在，否则跳过刷新
        if not self._is_logged_in():
            return
        controller = self._get_controller()
        if controller is None:
            return

        try:
            self.refresh_once()
            self._schedule_next()
        except Exception as e:
            # 失败时打印错误并停止定时器，避免异常循环
            print_error(f"定时刷新任务失败: {str(e)}")
            self.stop()

    def start(self):
        """对外启动：立即执行一次刷新并安排下一次"""
        if not self._is_logged_in():
            return
        try:
            # 立即刷新一次，确保状态及时更新
            self.refresh_once()
        except Exception as e:
            print_error(f"定时刷新任务失败: {str(e)}")
            self.stop()
            return
        # 刷新成功后安排下一次定时刷新
        self._schedule_next()
