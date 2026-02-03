from __future__ import annotations
from enum import Enum


class LoginState(str, Enum):
    """登录流程状态"""

    # 空闲状态：未开始任何登录流程
    IDLE = "idle"

    # 登录流程启动中：初始化浏览器、准备环境等
    STARTING = "starting"

    # 二维码已生成，可以对外展示
    QR_READY = "qr_ready"

    # 等待扫码 / 确认阶段
    WAIT_SCAN = "waiting"

    # 登录流程成功结束（过程成功，不代表永久有效）
    SUCCESS = "success"

    # 登录流程失败（明确失败，例如接口异常）
    FAILED = "failed"

    # 登录流程过期（例如二维码过期）
    EXPIRED = "expired"
