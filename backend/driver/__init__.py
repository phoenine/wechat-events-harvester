"""driver 包入口。

说明：
- 对外仅暴露 wx_service 的 Facade，避免导出边界不清晰。
- 不应在 import 阶段启动浏览器或触发重型副作用。
"""

from driver.wx.service import (
    WxService,
    get_qr_code,
    get_state,
    wait_until_finished,
    get_session_info,
    get_cookie_header,
    get_cookies_str,
    login_with_token,
    fetch_article,
    clear_session,
    logout,
    shutdown,
)

__all__ = [
    "WxService",
    "get_qr_code",
    "get_state",
    "wait_until_finished",
    "get_session_info",
    "get_cookie_header",
    "get_cookies_str",
    "login_with_token",
    "fetch_article",
    "clear_session",
    "logout",
    "shutdown",
]
