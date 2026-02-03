from core.integrations.wx.base import WxGather
from core.integrations.wx.modes.api import MpsApi
from core.integrations.wx.modes.app import MpsAppMsg
from core.integrations.wx.modes.web import MpsWeb

__all__ = [
    "WxGather",
    "MpsApi",
    "MpsAppMsg",
    "MpsWeb",
    "search_Biz",
]


def search_Biz(kw: str = "", limit: int = 10, offset: int = 0):
    """便捷入口：保持旧调用方式不变。"""
    return WxGather().search_Biz(kw, limit=limit, offset=offset)

if __name__ == "__main__":
    pass
